"""Test the recognition + assessment pipeline on a real worksheet image."""
import asyncio, sys, json, io
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.worksheet_recognizer import WorksheetRecognizer
from app.services.assessment_engine import assess
from app.services.image_processor import ImageProcessor

async def main():
    img_path = r"c:\xwechat_files\wxid_berzlxdxjjb922_5005\temp\RWTemp\2026-06\9e20f478899dc29eb19741386f9343c8\7364c561e3db61bd6297cf30ba0bbd9d.jpg"
    with open(img_path, 'rb') as f:
        img_data = f.read()
    print(f"Image size: {len(img_data)} bytes")

    proc = ImageProcessor()
    processed, fname = await proc.process(img_data, 'test2.jpg')
    print(f"Processed: {fname} ({len(processed)} bytes)")

    rec = WorksheetRecognizer()
    print(f"Calling Vision API (model={rec.model})...")
    result = await rec.analyze(processed, age_group='small')

    meta = result.pop('_meta', {})
    print(f"\n=== RECOGNITION ===")
    print(f"Model: {meta.get('model', '?')}")
    print(f"Tokens: {json.dumps(meta.get('usage', {}))}")
    print(f"Worksheet type: {result.get('worksheet_type')}")
    print(f"Problems ({len(result.get('problems', []))}):")
    for p in result.get('problems', []):
        status = "OK" if p['is_correct'] else "X"
        print(f"  {p['id']}: type={p['type']} | child={p['child_answer']} | expected={p['correct_answer']} | {status}")
    print(f"Preliminary scores: {json.dumps(result.get('dimension_scores_preliminary', {}), ensure_ascii=False)}")
    print(f"Observations: {json.dumps(result.get('observations', {}), ensure_ascii=False)[:500]}")

    assessment = await assess(result, 'small', '测试幼儿')
    print(f"\n=== ASSESSMENT ===")
    for dim in assessment['assessment']:
        print(f"  {dim['display_name']}: {dim['score']}% [{dim['level']}]")

    dp = assessment.get('dimension_problems', {})
    if dp:
        print(f"\n=== PER-DIMENSION ===")
        for dim_key, dim_data in dp.items():
            print(f"\n{dim_data['display_name']} ({dim_data['score']}%, {dim_data['correct_count']}/{dim_data['total_count']})")
            print(f"  Analysis: {dim_data['dimension_analysis'][:300]}")
            for p in dim_data['problems']:
                print(f"    {p['id']}: {p['type_name']} | ans={p['child_answer']} | {'OK' if p['is_correct'] else 'X'}")
    else:
        print("\n  (no dimension_problems — possibly incomplete)")

    print(f"\n=== OVERALL ===")
    print(assessment['overall_summary'][:500])

asyncio.run(main())
