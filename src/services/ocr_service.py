from functools import lru_cache
import cv2
import easyocr
import numpy as np
from src.config import get_settings


class OCRService:
    def __init__(self):
        settings = get_settings()
        self.reader = easyocr.Reader(settings.ocr_languages, gpu=settings.ocr_use_gpu)

    @staticmethod
    def decode_image(image_bytes: bytes) -> np.ndarray:
        array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image from bytes.")

        return image

    @staticmethod
    def preprocess(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        gray = cv2.bilateralFilter(gray, 7, 35, 35)
        return gray

    def extract_text(self, image_bytes: bytes) -> str:
        image = self.decode_image(image_bytes)
        processed_image = self.preprocess(image)
        results = self.reader.readtext(processed_image, detail=1, paragraph=False)

        lines = []

        for item in results:
            if len(item) < 3:
                continue

            text = str(item[1]).strip()
            confidence = float(item[2])

            if text and confidence >= 0.25:
                lines.append(text)

        return "\n".join(lines).strip()


@lru_cache
def get_ocr_service() -> OCRService:
    return OCRService()