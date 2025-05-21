import numpy as np
import cv2
from ultralytics import YOLO
from .function.process_frame import process_frame

# Load model YOLO 1 lần duy nhất khi import
plate_detector = YOLO("model/LP_detector.pt")
char_detector = YOLO("model/LP_ocr.pt")

def run_plate_recognition(image_bytes):
    """
    Nhận diện biển số từ ảnh (dạng bytes)
    Trả về: dict {"plate": "61A12345"}
    """

    # Giải mã ảnh từ bytes về OpenCV format
    image_np = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Không thể giải mã ảnh từ bytes.")

    # Gọi hàm xử lý ảnh đã có sẵn
    _, plate_text = process_frame(frame, plate_detector, char_detector)

    return {
        "plate": plate_text
    }
