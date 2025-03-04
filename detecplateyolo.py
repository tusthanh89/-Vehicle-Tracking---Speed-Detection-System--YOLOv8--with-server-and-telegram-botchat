import cv2
import pytesseract
import numpy as np
import base64
from ultralytics import YOLO

# Đường dẫn đến Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load model YOLO đã train cho biển số
model = YOLO('best.pt')  # Thay bằng đường dẫn tới model YOLO của bạn

def improved_recognize_license_plate(image):
    try:
        # Nhận diện biển số bằng YOLO với confidence thấp hơn
        results = model.predict(image, conf=0.5)  # Giảm confidence
        
        if len(results[0].boxes.data) > 0:
            boxes = results[0].boxes.data
            # Lọc ra các box có class là 0 (biển số)
            plate_boxes = [box for box in boxes if int(box[5]) == 0]
            
            if len(plate_boxes) > 0:
                box = plate_boxes[0]
                x1, y1, x2, y2 = map(int, box[:4])
                
                # Cắt vùng biển số
                roi = image[y1:y2, x1:x2]
                
                # Xử lý ROI để nhận diện tốt hơn
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                roi_resized = cv2.resize(roi_gray, None, fx=3, fy=2.2, interpolation=cv2.INTER_CUBIC)  # Giảm tỷ lệ resize
                
                _, roi_thresh = cv2.threshold(roi_resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Nhận diện ký tự bằng Tesseract
                custom_config = r'--oem 1 --psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                plate_text = pytesseract.image_to_string(roi_thresh, config=custom_config).strip()
                
                # Làm sạch kết quả OCR
                plate_text = ''.join(filter(str.isalnum, plate_text))
                
                return plate_text, roi
                
        return None, None
        
    except Exception as e:
        print(f"Lỗi trong quá trình nhận diện: {e}")
        return None, None

# Hàm để lưu biển số vào database
def save_license_plate_to_db(license_plate, image_license_data, conn, cursor):
    try:
        if conn is None or cursor is None:
            print("Kết nối database không hợp lệ")
            return False

        _, buffer = cv2.imencode('.jpg', image_license_data)
        byte_im = buffer.tobytes()
        image_base64 = base64.b64encode(byte_im).decode('utf-8')

        sql = "INSERT INTO license_plates (license_plate, image_license_data) VALUES (%s, %s)"
        cursor.execute(sql, (license_plate, image_base64))
        conn.commit()
        print(f"Đã lưu biển số {license_plate} thành công")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu biển số: {e}")
        if conn:
            conn.rollback()
        return False

# Hàm xử lý và lưu biển số
def process_and_save_plate(image, conn, cursor):
    try:
        if image is None:
            print("Ảnh đầu vào rỗng")
            return None, None

        detected_plate, plate_roi = improved_recognize_license_plate(image)

        if detected_plate and plate_roi is not None:
            if save_license_plate_to_db(detected_plate, plate_roi, conn, cursor):
                return detected_plate, plate_roi

        print("Không thể xử lý biển số")
        return None, None

    except Exception as e:
        print(f"Lỗi trong quá trình xử lý: {e}")
        return None, None

# # Thêm hàm main để test
# if __name__ == "__main__":
#     import cv2
    
#     # Test với ảnh
#     def test_with_image():
#         image_path = r"C:\Users\thanh\OneDrive\Máy tính\Desktop\KLTN\images\car_2024-12-11_04-44-20.png"
#         image = cv2.imread(image_path)
        
#         if image is None:
#             print("Không thể đọc ảnh")
#             return
            
#         plate_text, plate_roi = improved_recognize_license_plate(image)
        
#         if plate_text and plate_roi is not None:
#             print(f"Biển số: {plate_text}")
#             cv2.imshow('Original Image', image)
#             cv2.imshow('Plate ROI', plate_roi)
#             cv2.waitKey(0)
#         else:
#             print("Không tìm thấy biển số")
        
#         cv2.destroyAllWindows()
    
#     # Test với webcam
#     def test_with_camera():
#         cap = cv2.VideoCapture(0)
        
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 print("Không thể đọc frame từ camera")
#                 break
                
#             plate_text, plate_roi = improved_recognize_license_plate(frame)
            
#             if plate_text and plate_roi is not None:
#                 print(f"Biển số: {plate_text}")
#                 cv2.putText(frame, plate_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#                 cv2.imshow('Plate ROI', plate_roi)
                
#             cv2.imshow('Frame', frame)
            
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
        
#         cap.release()
#         cv2.destroyAllWindows()
    
    
    
    
#     test_with_image()
    
