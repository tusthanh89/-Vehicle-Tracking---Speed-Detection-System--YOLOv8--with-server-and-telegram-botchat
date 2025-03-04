import math

class Tracker:
    def __init__(self):
        # Lưu trữ tọa độ trung tâm của các đối tượng
        self.center_points = {}
        # Đếm số lượng IDs
        # Mỗi khi phát hiện một đối tượng mới, số lượng sẽ tăng lên một
        self.id_count = 0
        self.p=0

    def update(self, objects_rect):
        # Boxes và IDs của các đối tượng
        objects_bbs_ids = []

        # Lấy tọa độ trung tâm của đối tượng mới
        for rect in objects_rect:
            x, y, w, h, p= rect
            # print(x,y,w,h)
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            # Tìm xem đối tượng đã được phát hiện trước đó chưa
            same_object_detected = False
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])
                # print (dist)
                if ((dist <50 )) :
                    self.center_points[id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h,id,p])
                    same_object_detected = True
                    break

            # Nếu đối tượng mới được phát hiện, chúng ta gán ID cho đối tượng đó
            if same_object_detected is False:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count,self.p])
                self.id_count += 1

        # Làm sạch từ điển của tọa độ trung tâm để loại bỏ các ID không còn được sử dụng nữa
        new_center_points = {}
        for obj_bb_id in objects_bbs_ids:
            _, _, _, _, object_id,p = obj_bb_id
            center = self.center_points[object_id]
            new_center_points[object_id] = center
            
        # Cập nhật từ điển với các ID không còn được sử dụng bị loại bỏ
        self.center_points = new_center_points.copy()
        return objects_bbs_ids
