import time
import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
import cvzone
from tracker import*
import mysql.connector
import base64
from sshtunnel import SSHTunnelForwarder
from datetime import datetime
from detecplateyolo import process_and_save_plate  # Import hàm từ detectplate2.py

try:
    model = YOLO('yolov8n.pt')
    stream = cv2.VideoCapture('licence.mp4')

    # Cấu hình SSH và Database
    ssh_host = "192.168.1.110"
    ssh_username = "root"
    ssh_password = "tytyty6910"
    db_username = "jdbc"
    db_password = "tytyty6910"
    db_name = "vehicle"

    # Tạo SSH tunnel
    ssh_tunnel = SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=('0.0.0.0', 3306)
    )

    # Khởi động SSH tunnel
    ssh_tunnel.start()

    # Kết nối database qua SSH tunnel
    db_connection = mysql.connector.connect(
        host='127.0.0.1',
        port=ssh_tunnel.local_bind_port,
        user=db_username,
        password=db_password,
        database=db_name
    )
    cursor = db_connection.cursor()

    # Thêm biến để theo dõi ID đã lưu
    saved_vehicle_ids = set()

    def save_image_to_db(image, speed, vehicle_id):
        # Kiểm tra nếu ID này đã được lưu
        if vehicle_id in saved_vehicle_ids:
            return
        
        try:
            # Chuyển ảnh OpenCV sang định dạng bytes
            is_success, im_buf_arr = cv2.imencode(".jpg", image)
            byte_im = im_buf_arr.tobytes()
            
            # Chuyển bytes thành base64 string
            image_base64 = base64.b64encode(byte_im).decode('utf-8')
            
            # SQL để chèn ảnh
            sql = "INSERT INTO vehicle_images (image_data, capture_time, speed) VALUES (%s, NOW(), %s)"
            cursor.execute(sql, (image_base64, speed))
            db_connection.commit()
            
            # Thêm ID vào set đã lưu
            saved_vehicle_ids.add(vehicle_id)
            print(f"Đã lưu xe ID {vehicle_id} với tốc độ {speed} km/h")
        except Exception as e:
            print(f"Lỗi khi lưu ảnh: {e}")

    def RGB(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE :  
            colorsBGR = [x, y]
            print(colorsBGR)

    cv2.namedWindow('RGB')
    cv2.setMouseCallback('RGB', RGB)

    classnames = []
    counter_down=[]
    counter_up=[]
    down={}
    up={}

    #đọc file coco.txt
    my_file = open("coco.txt", "r")
    data = my_file.read()
    class_list = data.split("\n")
    #print(class_list)
    count=0
    count_up=0
    count_down=0
    #đọc file tracker 
    tracker =Tracker()
    #khai báo vị trí khi đối tượng đi qua đó sẽ nhận diện 
    area=[(26,86),(789,86),(992,333),(13,333)]
    greenline=(25,136),(830,136)
    #(489,267),(545,267)
    area3=[(25,136),(830,136),(992,333),(13,333)]
    a_speed_kh = 0 
    y=86
    z=330
    g=136
    offset = 7   
    while True:
        #đọc file vid dùng cái này    
        ret,frame = stream.read()
        if not ret:
            print("Không thể đọc frame")
            break

        # tang toc do vid cai nay xài nó đi nhanh quÁ ko đọc kịp frame đâm ra nhận diện kém  
        # count += 1
        # if count % 3 != 0:
        #     continue

        frame=cv2.resize(frame,(1020,500))
        
        results=model.predict(frame)
    #   print(results)
        a=results[0].boxes.data
        px=pd.DataFrame(a).astype("float")
        print(px)
        list=[]
        for index,row in px.iterrows():
    #        print(row)
        #vòng lập lấy tọa độ lớp và tỉ lệ % trong 1 frame ảnh
            x1=int(row[0]) #toạ độ x trên
            y1=int(row[1]) #tọa độ y trên
            x2=int(row[2]) #tọa đ x dưới
            y2=int(row[3]) #tọa độ y dưới 
            p=float(row[4]) # này để lấy %
            d=int(row[5]) # lớp
            c=class_list[d]
            if 'car'  in c:
                list.append([x1,y1,x2,y2,p])
        #update list        
        bbox_id=tracker.update(list)
        # vòng lặp để lấy tâm của đối tượng
        for bbox in bbox_id:
            x3,y3,x4,y4,id,p=bbox
            cx=int(x3+x4)//2
            cy=int(y3+y4)//2
            pp=p
            # print(f"cy: {cy}, y: {y}, z: {z}, pp: {pp}")
            # mặc định là -1 nếu đối tượng đi qua vùng này thì nó sẽ thành 0 và thêm id nó vào biến down            
            result=cv2.pointPolygonTest(np.array(area,np.int32),((cx,cy)),False)
            if result>=0:
                cv2.circle(frame,(cx,cy),4,(0,0,255),-1)
                cv2.rectangle(frame,(x3,y3),(x4,y4),(255,255,255),2)
                cvzone.putTextRect(frame,f'{c, (round(pp*100,2))}',(x3,y3),1,1)
            
            if y < (cy + offset) and y > (cy - offset):
                down[id]=time.time()
                # print(down[id])
               
            if id in down:
                    if z < (cy + offset) and z > (cy - offset)and pp>0.5: 
                        
                        if counter_down.count(id)==0:
                            counter_down.append(id)
                            
                    
                    if z < (cy + offset) and z > (cy - offset) and pp >0.5 and a_speed_kh>70: 
                        car_image = frame[y3:y4, x3:x4]
                        resized_car_image = cv2.resize(car_image, (500, 500))
                        
                        # Lưu ảnh xe
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        image_path = f"images/car_{timestamp}.png"
                        cv2.imwrite(image_path, resized_car_image)
                        
                        # Gọi hàm xử lý biển số từ detectplate2.py
                        detected_plate, plate_roi = process_and_save_plate(resized_car_image, db_connection, cursor)
                        
                        if detected_plate and plate_roi is not None:
                            # Lưu ảnh biển số để debug
                            cv2.imwrite(f"images/plate_{timestamp}.jpg", plate_roi)
                        
                        # Lưu thông tin xe vào bảng vehicle_images
                        save_image_to_db(resized_car_image, a_speed_kh, id)
                    if g < (cy + offset) and g > (cy - offset)and pp>0.5:
                        distance=30 #meters
                        elapsed_time=time.time() - down[id]
                        a_speed_ms = distance / elapsed_time
                        a_speed_kh = a_speed_ms * 3.6
            result1=cv2.pointPolygonTest(np.array(area3,np.int32),((cx,cy)),False)
            if result1>=0:
                cv2.putText(frame,str(int(a_speed_kh))+'Km/h',(x4,y4 ),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,255,255),2) 
        #màu mè hoa lá hẹ 
        
        
        text_color = (255,255,255)  # white color for text
        green_color = (0, 255, 0)  # (B, G, R)
        red_color = (0, 0, 255)  # (B, G, R)   
        blue_color = (255, 0, 0)  # (B, G, R) 
        
        cv2.line(frame,(26,y),(789,y),red_color,3)  #  starting cordinates and end of line cordinates
        cv2.putText(frame,('detect'),(29,86),cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
        cv2.line(frame,(25,g),(830,g),green_color,3)  #  starting cordinates and end of line cordinates
        cv2.putText(frame,('begin show speed'),(25,136),cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
        # cv2.line(frame,(532,323),(788,323),green_color,3)  #  starting cordinates and end of line cordinates
        # cv2.putText(frame,('begin show speed'),(532,323),cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
        cv2.line(frame,(70,333),(857,333),blue_color,3)  # seconde line
        cv2.putText(frame,('end and count'),(70,360),cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)  

        # 2 dòng này vẽ cái khung khi đối tượng đi dô để detect cho dễ nhìn
        # cv2.polylines(frame,[np.array(area,np.int32)],True,(255,255,255),2)
        # cv2.polylines(frame,[np.array(area2,np.int32)],True,(0,255,0),2)
        # cv2.polylines(frame,[np.array(area3,np.int32)],True,(255,255,255),2)
        # cv2.polylines(frame,[np.array(area4,np.int32)],True,(0,255,0),2)

        #dùng hàm len() để đếm và vẽ lên màn hình 
        downwards = (len(counter_down))
        cv2.putText(frame,('going down - ')+ str(downwards),(60,40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, green_color, 1, cv2.LINE_AA)    
        cv2.imshow("RGB", frame)

        # In ra các giá trị quan trọng
       

        if cv2.waitKey(1)&0xFF==27:
            print("Người dùng đã thoát")
            break

# except Exception as e:
#     print(f"Lỗi: {e}")

finally:
    print("Đang dọn dẹp tài nguyên...")
    try:
        stream.release()
        cv2.destroyAllWindows()
        cursor.close()
        db_connection.close()
        ssh_tunnel.stop()
    except Exception as e:
        print(f"Lỗi khi dọn dẹp: {e}")
