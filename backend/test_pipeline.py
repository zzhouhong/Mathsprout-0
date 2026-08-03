"""Batch test the recognition pipeline on multiple worksheet images."""
import asyncio, sys, json, io
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.worksheet_recognizer import WorksheetRecognizer
from app.services.assessment_engine import assess
from app.services.image_processor import ImageProcessor

IMAGES = [
    r"c:\xwechat_files\wxid_berzlxdxjjb922_5005\temp\RWTemp\2026-06\9e20f478899dc29eb19741386f9343c8\d6e9be1d97cc0db6462c1de2d69f5bbb.jpg",
    r"c:\xwechat_files\wxid_berzlxdxjjb922_5005\temp\RWTemp\2026-06\9e20f478899dc29eb19741386f9343c8\4814ab44157c80dfe1f7cac5ed93e09b.jpg",
]

async def analyze_one(img_path: str, index: int):
    print(f"\n{'='*60}")
    print(f"IMAGE {index}: {img_path.split(chr(92))[-1][:40]}...")
    print(f"{'='*60}")

    with open(img_path, 'rb') as f:
        img_data = f.read()
    print(f"Size: {len(img_data)} bytes")

    proc = ImageProcessor()
    processed, fname = await proc.process(img_data, f'test{index}.jpg')

    rec = WorksheetRecognizer()
    result = await rec.analyze(processed, age_group='small')

    meta = result.pop('_meta', {})
    ws_type = result.get('worksheet_type', '?')
    learning_obj = result.get('observations', {}).get('learning_objective', '未提取')
    print(f"Type: {ws_type} | Tokens: {meta.get('usage', {}).get('total_tokens', '?')}")
    print(f"Learning objective: {learning_obj}")

    problems = result.get('problems', [])
    print(f"Problems ({len(problems)}):")
    for p in problems:
        status = "OK" if p['is_correct'] else "X"
        print(f"  {p['id']}: type={p['type']} | child={p['child_answer']} | expected={p['correct_answer']} | {status}")

    if ws_type == 'incomplete' or not problems:
        print("→ EMPTY/INCOMPLETE — skipping assessment")
        return

    assessment = await assess(result, 'small', '测试幼儿')
    print(f"\nScores:")
    for dim in assessment['assessment']:
        if dim['score_details']['total'] > 0:
            print(f"  {dim['display_name']}: {dim['score']}% [{dim['level']}] ({dim['score_details']['correct']}/{dim['score_details']['total']})")

    dp = assessment.get('dimension_problems', {})
    if dp:
        for dim_key, dim_data in dp.items():
            print(f"  → {dim_data['dimension_analysis'][:200]}")

async def main():
    for i, path in enumerate(IMAGES, 1):
        try:
            await analyze_one(path, i)
        except Exception as e:
            print(f"ERROR: {e}")

asyncio.run(main())
