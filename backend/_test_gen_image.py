"""Generate a simple test math worksheet image."""
from PIL import Image, ImageDraw, ImageFont
import os

img = Image.new("RGB", (800, 600), color=(255, 255, 255))
draw = ImageDraw.Draw(img)

draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=2)
draw.text((400, 40), "Math Worksheet - Counting", fill=(0, 0, 0), anchor="mt")

for i in range(5):
    y = 100 + i * 90
    draw.text((50, y), f"{i+1}.", fill=(0, 0, 0))
    draw.ellipse([80, y - 15, 100, y + 5], outline=(0, 100, 200), width=2)
    draw.text((120, y - 8), "___ apples", fill=(100, 100, 100))
    draw.text((600, y - 8), str(i + 1), fill=(0, 0, 0))

out_path = os.path.join(os.getcwd(), "_test_worksheet.png")
img.save(out_path, "PNG")
print(f"Test image created: {out_path} ({os.path.getsize(out_path)} bytes)")
