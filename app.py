from flask import Flask, render_template, Response, send_file, request, redirect, url_for, jsonify
import mysql.connector
import base64
from sshtunnel import SSHTunnelForwarder


app = Flask(__name__)

# Cấu hình SSH và Database
ssh_host = "192.168.159.129"
ssh_username = "thanhtu"
ssh_password = "tytyty6910"
db_username = "jdbc"
db_password = "tytyty6910"
db_name = "vehicle"

def get_db_connection():
    ssh_tunnel = SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=('0.0.0.0', 3306)
    )
    
    ssh_tunnel.start()
    
    connection = mysql.connector.connect(
        host='127.0.0.1',
        port=ssh_tunnel.local_bind_port,
        user=db_username,
        password=db_password,
        database=db_name
    )
    return connection, ssh_tunnel

@app.route('/')
def index():
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                vi.id, 
                vi.capture_time, 
                vi.speed,
                lp.id as license_plate_id, 
                lp.license_plate, 
                lp.image_license_data,
                vd.phone_number,
                vd.citizen_id,
                vd.address,
                vd.personal_image_data
            FROM vehicle_images vi
            LEFT JOIN license_plates lp ON vi.capture_time = lp.capture_time
            LEFT JOIN vehicle_details vd ON lp.license_plate = vd.license_plate
            ORDER BY vi.capture_time DESC
        """)
        vehicles = cursor.fetchall()
        
        # Debug: In ra thông tin về ảnh
        for vehicle in vehicles:
            if vehicle['image_license_data']:
                print(f"License plate image data exists for ID: {vehicle['id']}")
                print(f"First 50 chars: {vehicle['image_license_data'][:50]}")
                
        return render_template('index.html', vehicles=vehicles)
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

@app.route('/vehicle_image/<int:id>')
def get_vehicle_image(id):
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(buffered=True)
    
    try:
        cursor.execute("SELECT image_data FROM vehicle_images WHERE id = %s", (id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                # Decode base64 thành binary
                image_binary = base64.b64decode(result[0])
                return Response(
                    image_binary,
                    mimetype='image/jpeg',
                    headers={
                        'Content-Type': 'image/jpeg',
                        'Cache-Control': 'no-cache'
                    }
                )
            except Exception as e:
                print(f"Lỗi khi decode ảnh xe: {e}")
                return Response(status=500)
        return Response(status=404)
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

@app.route('/plate_image/<int:id>')
def get_plate_image(id):
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(buffered=True)
    
    try:
        cursor.execute("SELECT image_license_data FROM license_plates WHERE id = %s", (id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                # Decode base64 thành binary
                image_binary = base64.b64decode(result[0])
                return Response(
                    image_binary,
                    mimetype='image/jpeg',
                    headers={
                        'Content-Type': 'image/jpeg',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                )
            except Exception as e:
                print(f"Lỗi khi decode ảnh biển số: {e}")
                return Response(status=500)
        return Response(status=404)
    except Exception as e:
        print(f"Lỗi khi lấy ảnh biển số: {e}")
        return Response(status=500)
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

@app.route('/license_plate_image/<int:id>')
def get_license_plate_image(id):
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(buffered=True)
    
    try:
        cursor.execute("SELECT image_license_data FROM license_plates WHERE id = %s", (id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                # Decode base64 thành binary
                image_binary = base64.b64decode(result[0])
                return Response(
                    image_binary,
                    mimetype='image/jpeg',
                    headers={
                        'Content-Type': 'image/jpeg',
                        'Cache-Control': 'no-cache'
                    }
                )
            except Exception as e:
                print(f"Lỗi khi decode ảnh biển số: {e}")
                return Response(status=500)
        return Response(status=404)
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

@app.route('/edit_license_plate/<int:id>', methods=['POST'])
def edit_license_plate(id):
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        data = request.get_json()
        new_license_plate = data['license_plate']
        cursor.execute("UPDATE license_plates SET license_plate = %s WHERE id = %s", 
                     (new_license_plate, id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Lỗi khi cập nhật biển số: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

@app.route('/send_message/<int:id>', methods=['POST'])
def send_message(id):
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        data = request.get_json()
        message = data['message']
        # Thêm logic gửi tin nhắn ở đây
        print(f"Đã gửi tin nhắn cho ID {id}: {message}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Lỗi khi gửi tin nhắn: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
