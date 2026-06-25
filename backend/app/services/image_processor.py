"""
Image preprocessing pipeline using OpenCV and Pillow.

Steps:
1. Format unification: all inputs → PNG (including PDF first-page render)
2. CLAHE contrast enhancement (pencil marks on paper can be faint)
3. Deskew / rotation correction
4. Sharpening
5. Resolution adaptation (target 1080p, max 2576px for Claude)
"""

import asyncio
import concurrent.futures
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Optional, Tuple
import io
import logging
import functools

logger = logging.getLogger(__name__)

# Shared thread pool for CPU-bound image processing
_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)

# Quality profile → target pixel size mapping
IMAGE_SIZE_PROFILES = {
    "fast": 720,
    "balanced": 1080,
    "accurate": 1440,
}


def resolve_image_size(profile: str, fallback: int = 1080) -> int:
    """Map a quality profile name to its target pixel size."""
    return IMAGE_SIZE_PROFILES.get(profile, fallback)


def _run_sync(fn):
    """Decorator: offload a sync method to the thread pool."""
    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            _THREAD_POOL, lambda: fn(self, *args, **kwargs)
        )
    return wrapper


class ImageProcessor:
    def __init__(
        self,
        target_size_px: int = 1080,
        max_size_px: int = 2576,
        quality: int = 85,
    ):
        self.target_size = target_size_px
        self.max_size = max_size_px
        self.quality = quality

    async def process(
        self,
        input_data: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """Main processing pipeline. Offloads all CPU work to thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            _THREAD_POOL,
            self._process_sync,
            input_data, filename, content_type,
        )

    def _process_sync(
        self,
        input_data: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """Synchronous processing — runs in thread pool."""
        is_pdf = (
            content_type == "application/pdf"
            or filename.lower().endswith(".pdf")
            or input_data[:4] == b"%PDF"
        )

        if is_pdf:
            image = self._pdf_to_image_sync(input_data)
        else:
            image = self._load_image(input_data)

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = self._deskew(image)
        image = self._clahe_enhance(image)
        image = self._sharpen(image)
        image = self._resize(image)

        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        output.seek(0)

        out_filename = Path(filename).stem + "_processed.png"
        return output.read(), out_filename

    def _load_image(self, data: bytes) -> Image.Image:
        """Load image from bytes, handling various formats."""
        image = Image.open(io.BytesIO(data))
        # Auto-rotate based on EXIF
        try:
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass
        return image

    def _pdf_to_image_sync(self, data: bytes) -> Image.Image:
        """Synchronous version — runs in thread pool."""
        # Try pdf2image first
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(data, dpi=200, first_page=1, last_page=1)
            if images:
                logger.info("PDF rendered via pdf2image (200 DPI)")
                return images[0]
        except ImportError:
            logger.debug("pdf2image not installed, trying PyMuPDF...")
        except Exception as e:
            logger.warning(f"pdf2image conversion failed: {e}")

        # Try PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(stream=data, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            logger.info("PDF rendered via PyMuPDF (200 DPI)")
            return img
        except ImportError:
            logger.debug("PyMuPDF not installed.")
        except Exception as e:
            logger.warning(f"PyMuPDF conversion failed: {e}")

        # Fallback: return a placeholder image
        logger.error("No PDF backend available (pdf2image or PyMuPDF required)")
        return Image.new("RGB", (800, 600), color=(255, 255, 240))

    async def _pdf_to_image(self, data: bytes) -> Image.Image:
        """
        Render the first page of a PDF as a PIL Image.

        Tries multiple backends:
        1. pdf2image (preferred — best quality)
        2. PyMuPDF (fitz)
        3. Falls back to an error image if neither is available
        """
        # Try pdf2image first
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(data, dpi=200, first_page=1, last_page=1)
            if images:
                logger.info("PDF rendered via pdf2image (200 DPI)")
                return images[0]
        except ImportError:
            logger.debug("pdf2image not installed, trying PyMuPDF...")
        except Exception as e:
            logger.warning(f"pdf2image conversion failed: {e}")

        # Try PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=data, filetype="pdf")
            if doc.page_count > 0:
                page = doc[0]
                # Render at 200 DPI
                mat = fitz.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
                logger.info(f"PDF rendered via PyMuPDF at {pix.width}x{pix.height}")
                return image
            doc.close()
        except ImportError:
            logger.debug("PyMuPDF not installed.")
        except Exception as e:
            logger.warning(f"PyMuPDF conversion failed: {e}")

        # Fallback: generate an error placeholder
        logger.error("No PDF backend available. Install pdf2image or PyMuPDF.")
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        # Draw a simple error indicator
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            draw.text(
                (400, 280),
                "PDF support requires pdf2image or PyMuPDF",
                fill=(200, 50, 50),
                anchor="mm",
            )
            draw.text(
                (400, 320),
                "pip install pdf2image  or  pip install PyMuPDF",
                fill=(100, 100, 100),
                anchor="mm",
            )
        except Exception:
            pass
        return img

    def _deskew(self, image: Image.Image) -> Image.Image:
        """
        Detect and correct skew angle using OpenCV.
        Uses Hough Line Transform on edge-detected image.
        """
        # Convert to OpenCV format
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough Line Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

        if lines is None:
            return image  # No strong lines detected, skip deskew

        # Calculate median angle
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90  # Convert to degrees from horizontal
            # Only consider near-horizontal or near-vertical lines
            if -45 < angle < 45:
                angles.append(angle)

        if not angles:
            return image

        median_angle = np.median(angles)

        # Only correct if angle is significant (> 0.3 degrees)
        if abs(median_angle) < 0.3:
            return image

        # Rotate image to correct skew
        return image.rotate(
            median_angle, expand=False, resample=Image.BICUBIC, fillcolor="white"
        )

    def _clahe_enhance(self, image: Image.Image) -> Image.Image:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        # Convert to OpenCV format
        img_np = np.array(image)

        # Convert to LAB color space for luminance-based enhancement
        lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE to luminance channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel_enhanced = clahe.apply(l_channel)

        # Merge channels back
        lab_enhanced = cv2.merge([l_channel_enhanced, a_channel, b_channel])
        enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)

        return Image.fromarray(enhanced)

    def _sharpen(self, image: Image.Image) -> Image.Image:
        """Apply mild sharpening to enhance pencil marks."""
        # Use unsharp mask for better quality
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(1.5)

    def _resize(self, image: Image.Image) -> Image.Image:
        """
        Resize image to target size while respecting max limit.
        - Target: 1080p on the long edge
        - Max: 2576px (Claude API limit)
        - Maintain aspect ratio
        """
        w, h = image.size
        long_edge = max(w, h)

        # Already within target, no resize needed
        if long_edge <= self.target_size:
            return image

        # Calculate new size
        target = min(self.target_size, self.max_size)
        scale = target / long_edge
        new_w = int(w * scale)
        new_h = int(h * scale)

        return image.resize((new_w, new_h), resample=Image.LANCZOS)
