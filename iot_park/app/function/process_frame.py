from .sort_charater import sort_by_rows
import cv2

def process_frame(frame, plate_detector, char_detector):
    """
    Nhận diện biển số từ frame.
    Trả về: plate_text (str)
    """
    plate_results = plate_detector(frame)
    plate_text = ""

    for plate in plate_results[0].boxes.xyxy:
        x1, y1, x2, y2 = map(int, plate.tolist())
        plate_img = frame[y1:y2, x1:x2].copy()

        if plate_img is None or plate_img.size == 0:
            continue

        char_results = char_detector(plate_img)
        detected_chars = []

        for box, conf, cls in zip(char_results[0].boxes.xyxy, char_results[0].boxes.conf, char_results[0].boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box.tolist())
            label = char_results[0].names[int(cls)]

            if conf > 0.5:
                detected_chars.append(((x_min, y_min, y_max), label))

        plate_text = sort_by_rows(detected_chars)
        break  # chỉ xử lý 1 biển số đầu tiên

    return plate_text
