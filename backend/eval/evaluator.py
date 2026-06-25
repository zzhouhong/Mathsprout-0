"""
评估WorksheetRecognizer识别准确率。
对比AI识别结果与人工标注的真实答案，输出量化指标。
"""

import json
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from app.services.worksheet_recognizer import WorksheetRecognizer


@dataclass
class ProblemResult:
    """单道题的评估结果"""
    problem_id: str
    type: str
    predicted_answer: str
    ground_truth_answer: str
    is_correct: bool           # AI判断的正确性
    ground_truth_correct: bool # 实际正确性
    confidence: float
    answer_match: bool         # 答案是否匹配（比is_correct更客观）


@dataclass
class ImageEvalResult:
    """单张图片的评估结果"""
    image_name: str
    age_group: str
    expected_type: str
    predicted_type: str
    type_match: bool
    problem_results: list[ProblemResult] = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def total_problems(self) -> int:
        return len(self.problem_results)

    @property
    def answer_accuracy(self) -> float:
        """答案识别准确率（AI读出的答案 vs 真实答案）"""
        if not self.problem_results:
            return 0.0
        matched = sum(1 for p in self.problem_results if p.answer_match)
        return matched / len(self.problem_results)

    @property
    def correctness_accuracy(self) -> float:
        """对错判断准确率（AI判断对错 vs 真实对错）"""
        if not self.problem_results:
            return 0.0
        matched = sum(1 for p in self.problem_results if p.is_correct == p.ground_truth_correct)
        return matched / len(self.problem_results)


@dataclass
class EvalReport:
    """整体评估报告"""
    total_images: int = 0
    total_problems: int = 0
    image_results: list[ImageEvalResult] = field(default_factory=list)
    overall_answer_accuracy: float = 0.0
    overall_correctness_accuracy: float = 0.0
    avg_confidence: float = 0.0
    total_tokens: int = 0
    dimension_breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "总图片数": self.total_images,
            "总题目数": self.total_problems,
            "答案识别准确率": f"{self.overall_answer_accuracy:.1%}",
            "对错判断准确率": f"{self.overall_correctness_accuracy:.1%}",
            "平均置信度": f"{self.avg_confidence:.2f}",
            "总Token消耗": self.total_tokens,
            "各维度表现": self.dimension_breakdown,
            "逐图详情": [
                {
                    "图片": r.image_name,
                    "题型匹配": "✅" if r.type_match else f"❌ (预测:{r.predicted_type}, 实际:{r.expected_type})",
                    "答案准确率": f"{r.answer_accuracy:.1%}",
                    "对错准确率": f"{r.correctness_accuracy:.1%}",
                    "题目数": r.total_problems,
                    "错误": r.errors,
                }
                for r in self.image_results
            ],
        }


class AccuracyEvaluator:
    """识别准确率评估器"""

    def __init__(self):
        self.recognizer = WorksheetRecognizer()

    async def evaluate_image(
        self,
        image_path: Path,
        ground_truth: dict,
        age_group: str = "middle",
    ) -> ImageEvalResult:
        """
        评估单张图片的识别准确率。

        Args:
            image_path: 操作单图片路径
            ground_truth: 人工标注的真实数据
                {
                    "worksheet_type": "counting",
                    "age_group": "middle",
                    "problems": [
                        {"id": "P1", "type": "counting", "correct_answer": "5", "is_correct": true},
                        ...
                    ]
                }
            age_group: 年龄段
        """
        result = ImageEvalResult(
            image_name=image_path.name,
            age_group=age_group,
            expected_type=ground_truth.get("worksheet_type", "unknown"),
            predicted_type="unknown",
            type_match=False,
        )

        try:
            # 读取图片
            image_data = image_path.read_bytes()

            # 调用识别API
            vision_result = await self.recognizer.analyze(
                image_data,
                age_group=age_group,
                use_cache=False,  # 不用缓存，确保每次都是真实调用
            )

            # 题型匹配
            result.predicted_type = vision_result.get("worksheet_type", "unknown")
            result.type_match = (
                result.predicted_type == result.expected_type
            )

            # Token消耗
            meta = vision_result.get("_meta", {})
            usage = meta.get("usage", {})
            result.token_usage = {
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
                "total": usage.get("total_tokens", 0),
            }

            # 逐题对比
            gt_problems = ground_truth.get("problems", [])
            pred_problems = vision_result.get("problems", [])

            # 建立题目ID映射
            gt_by_id = {p["id"]: p for p in gt_problems}
            pred_by_id = {p.get("id", ""): p for p in pred_problems}

            all_ids = set(gt_by_id.keys()) | set(pred_by_id.keys())

            for pid in sorted(all_ids):
                gt = gt_by_id.get(pid)
                pred = pred_by_id.get(pid)

                if gt and pred:
                    result.problem_results.append(ProblemResult(
                        problem_id=pid,
                        type=gt.get("type", "unknown"),
                        predicted_answer=str(pred.get("child_answer", "")),
                        ground_truth_answer=str(gt.get("correct_answer", "")),
                        is_correct=pred.get("is_correct", False),
                        ground_truth_correct=gt.get("is_correct", True),
                        confidence=pred.get("confidence", 0.0),
                        answer_match=(
                            str(pred.get("child_answer", "")).strip()
                            == str(gt.get("correct_answer", "")).strip()
                        ),
                    ))
                elif gt and not pred:
                    # AI漏识别
                    result.errors.append(f"漏识别题目 {pid}")
                elif pred and not gt:
                    # AI多识别（不算错误，但记录）
                    pass

        except Exception as e:
            result.errors.append(f"识别异常: {str(e)}")

        return result

    async def evaluate_batch(
        self,
        image_dir: Path,
        ground_truth_file: Path,
        age_group: str = "middle",
    ) -> EvalReport:
        """
        批量评估一个目录下的所有操作单。

        Args:
            image_dir: 图片目录
            ground_truth_file: 标注文件（JSON），格式见 ground_truth_template.json
            age_group: 默认年龄段（可被标注文件中的per-image设置覆盖）
        """
        # 加载标注
        gt_data = json.loads(ground_truth_file.read_text(encoding="utf-8"))
        images_gt = gt_data.get("images", [])

        # 按文件名索引
        gt_by_file = {img["filename"]: img for img in images_gt}

        # 遍历图片
        image_files = sorted(
            [f for f in image_dir.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        )

        results = []
        for img_path in image_files:
            gt = gt_by_file.get(img_path.name)
            if not gt:
                print(f"  ⚠️  跳过（无标注）: {img_path.name}")
                continue

            img_age = gt.get("age_group", age_group)
            print(f"  🔍 分析中: {img_path.name} (年龄段: {img_age})...")
            result = await self.evaluate_image(img_path, gt, img_age)

            if result.errors:
                for err in result.errors:
                    print(f"    ❌ {err}")
            print(
                f"    📊 答案准确率: {result.answer_accuracy:.1%}  "
                f"对错准确率: {result.correctness_accuracy:.1%}  "
                f"题型匹配: {'✅' if result.type_match else '❌'}"
            )
            results.append(result)

        # 汇总报告
        return self._build_report(results)

    def _build_report(self, results: list[ImageEvalResult]) -> EvalReport:
        report = EvalReport()
        report.image_results = results
        report.total_images = len(results)

        all_problems = []
        for r in results:
            all_problems.extend(r.problem_results)

        report.total_problems = len(all_problems)

        if all_problems:
            report.overall_answer_accuracy = (
                sum(1 for p in all_problems if p.answer_match) / len(all_problems)
            )
            report.overall_correctness_accuracy = (
                sum(1 for p in all_problems if p.is_correct == p.ground_truth_correct)
                / len(all_problems)
            )
            report.avg_confidence = (
                sum(p.confidence for p in all_problems) / len(all_problems)
            )

        # 按维度拆分
        dims = {}
        for p in all_problems:
            dim = p.type
            if dim not in dims:
                dims[dim] = {"total": 0, "answer_correct": 0, "correctness_correct": 0}
            dims[dim]["total"] += 1
            if p.answer_match:
                dims[dim]["answer_correct"] += 1
            if p.is_correct == p.ground_truth_correct:
                dims[dim]["correctness_correct"] += 1

        for dim, stats in dims.items():
            report.dimension_breakdown[dim] = {
                "题目数": stats["total"],
                "答案识别准确率": f"{stats['answer_correct'] / stats['total']:.1%}",
                "对错判断准确率": f"{stats['correctness_correct'] / stats['total']:.1%}",
            }

        # Token汇总
        report.total_tokens = sum(
            r.token_usage.get("total", 0) for r in results
        )

        return report


async def run_evaluation(image_dir: str, ground_truth_file: str, age_group: str = "middle") -> EvalReport:
    """便捷入口：运行评估并返回报告"""
    evaluator = AccuracyEvaluator()
    return await evaluator.evaluate_batch(
        Path(image_dir), Path(ground_truth_file), age_group
    )
