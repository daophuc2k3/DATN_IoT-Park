import cv2
from ultralytics import YOLO
from function.process_frame import process_frame
import sys

def process_image(image_path, output_path, plate_detector, char_detector):
    """Xử lý ảnh đầu vào"""
    frame = cv2.imread(image_path)
    if frame is None:
        raise ValueError("Không thể đọc ảnh. Kiểm tra đường dẫn!")

    processed_frame = process_frame(frame, plate_detector, char_detector)
    
    # Lưu ảnh kết quả
    cv2.imwrite(output_path, processed_frame)
    print(f"✅ Ảnh kết quả đã được lưu tại {output_path}")
    
    # Hiển thị kết quả
    cv2.imshow('License Plate Recognition', processed_frame)
    cv2.waitKey()
    cv2.destroyAllWindows()

def process_video(video_path, output_path, plate_detector, char_detector, save_output=True):
    """Xử lý video đầu vào hoặc webcam
    
    Args:
        video_path (str): Đường dẫn đến file video. Nếu là None thì sử dụng webcam
        output_path (str): Đường dẫn lưu file kết quả
        plate_detector: Model phát hiện biển số xe
        char_detector: Model nhận dạng ký tự
        save_output (bool): Có lưu output hay không (mặc định: True)
    """
    # Khởi tạo video capture
    if video_path is None:  # Sử dụng webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise ValueError("❌ Không thể mở camera!")
        print("✅ Đã kết nối camera thành công!")
    else:  # Sử dụng video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Không thể đọc video. Kiểm tra đường dẫn!")

    # Lấy thông tin video
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Tạo video writer nếu cần lưu output
    out = None
    if save_output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    print("✅ Đang xử lý video...")
    print("Nhấn 'q' để thoát")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Không thể đọc frame!")
                break

            processed_frame = process_frame(frame, plate_detector, char_detector)
            
            # Lưu frame nếu cần
            if save_output and out is not None:
                out.write(processed_frame)
            
            # Hiển thị frame
            cv2.imshow('License Plate Recognition', processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        print("\n⚠ Đã dừng xử lý video theo yêu cầu người dùng")
    finally:
        # Giải phóng tài nguyên
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        if save_output:
            print(f"✅ Video kết quả đã được lưu tại {output_path}")