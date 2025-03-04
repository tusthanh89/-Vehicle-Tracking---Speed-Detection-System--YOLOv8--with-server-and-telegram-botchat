import cv2
import pytesseract
import numpy as np
import base64

# Đường dẫn đến Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def improved_recognize_license_plate(image):
    # Resize ảnh để chuẩn hóa kích thước
    image = cv2.resize(image, (800, 600))
    
    # 1. Chuyển đổi ảnh sang ảnh xám
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. Tăng cường độ tương phản bằng CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    
    # 3. Làm mờ ảnh để giảm nhiễu
    blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
    
    # 4. Phát hiện cạnh bằng Canny edge detection
    edges = cv2.Canny(blurred, 50, 200)
    
    # 5. Phép toán morphology để nối các cạnh
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
    morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    # 6. Tìm các đường viền
    contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Lọc và tìm ROI có khả năng là biển số
    plate_contour = None
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        area = cv2.contourArea(contour)
        if 2000 < area < 25000 and 2.0 < aspect_ratio < 5.0:
            plate_contour = (x, y, w, h)
        break
    
    if plate_contour:
        x, y, w, h = plate_contour
        roi = image[y:y+h, x:x+w]
        
        # Xử lý ROI để nhận diện tốt hơn
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        roi_resized = cv2.resize(roi_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        
        _, roi_thresh = cv2.threshold(roi_resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Nhận diện ký tự bằng Tesseract
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        plate_text = pytesseract.image_to_string(roi_thresh, config=custom_config).strip()
        
        # Làm sạch kết quả OCR
        plate_text = ''.join(filter(str.isalnum, plate_text))
        
        return plate_text, roi
    else:
        return None, None

def save_license_plate_to_db(license_plate, image_license_data, conn, cursor):
    try:
        # Chuyển đổi hình ảnh thành dữ liệu nhị phân
        _, buffer = cv2.imencode('.jpg', image_license_data)
        byte_im = buffer.tobytes()
        
        # Chuyển bytes thành base64 string
        image_base64 = base64.b64encode(byte_im).decode('utf-8')

        # SQL để chèn biển số và dữ liệu hình ảnh vào bảng license_plates
        sql = "INSERT INTO license_plates (license_plate, image_license_data) VALUES (%s, %s)"
        cursor.execute(sql, (license_plate, image_base64))
        conn.commit()
        print(f"Đã lưu biển số {license_plate} và dữ liệu hình ảnh vào cơ sở dữ liệu.")
    except Exception as e:
        print(f"Lỗi khi lưu biển số: {e}")

def process_and_save_plate(image, conn, cursor):
    # Nhận diện biển số
    detected_plate, plate_roi = improved_recognize_license_plate(image)
    
    # Kiểm tra kết quả và lưu thông tin nếu có biển số
    if detected_plate and plate_roi is not None:
        print(f"Biển số nhận diện được: {detected_plate}")
        save_license_plate_to_db(detected_plate, plate_roi, conn, cursor)
        return detected_plate, plate_roi
    else:
        print("Không tìm thấy biển số trong ảnh.")
        return None, None
