# Vision Recognition Golden Set

每张操作单图片 + 一个 `expected.json` = 一个 golden case。

## 目录结构

```
golden/
  case-name-01/
    image.png          # 操作单照片
    expected.json      # 期望的识别结果
  case-name-02/
    image.jpg
    expected.json
```

## expected.json 格式

```json
{
  "age_group": "middle",
  "child_name": "测试幼儿",
  "expected": {
    "worksheet_type": "mixed",
    "problem_count": {"min": 5, "max": 10},
    "dimensions_covered": ["counting", "shapes_space"],
    "at_least_one_correct": true,
    "problems": [
      {
        "id": "P1",
        "type": "counting",
        "child_answer_match": "3",
        "correct_answer_match": "5"
      }
    ]
  },
  "tolerance": {
    "min_dimensions_scored": 1,
    "max_unrecognized_ratio": 0.5
  }
}
```

## 如何添加新的 golden case

### 方法 1：用 build_golden.py 辅助生成

```bash
cd backend
.\venv\Scripts\python.exe build_golden.py --image path/to/your/worksheet.jpg --name "counting-basic"
```

脚本会跑识别管线，然后交互式让你确认/修正每个字段，最后保存到 `tests/images/golden/counting-basic/`。

### 方法 2：手动创建

1. 将操作单照片复制到 `golden/<case-name>/image.png`
2. 用 `vision_eval.py` 跑一次识别看结果：
   ```bash
   .\venv\Scripts\python.exe vision_eval.py --image golden/<case-name>/image.png --format json
   ```
3. 根据输出手动编写 `expected.json`

## 测试运行

```bash
cd backend
python -m pytest tests/test_vision_golden.py -v
```

## 断言策略

Golden set 测试**不要求精确匹配**（视觉识别有随机性），而是验证：
- 题型数量在预期范围内
- 指定维度被覆盖
- 至少有一个题目被正确识别
- 未识别比例不超过阈值
- 具体答案用模糊匹配（数字提取 + 包含比较）
