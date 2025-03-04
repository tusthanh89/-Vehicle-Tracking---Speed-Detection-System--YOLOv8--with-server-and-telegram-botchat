import mysql.connector
import telegram
import base64
from sshtunnel import SSHTunnelForwarder
import io
from datetime import datetime

# Cấu hình SSH và Database
ssh_host = "192.168.1.115"
ssh_username = "root"
ssh_password = "tytyty6910"
db_username = "jdbc"
db_password = "tytyty6910"
db_name = "vehicle"

# Cấu hình Telegram Bot
TELEGRAM_BOT_TOKEN = '7921391713:AAGiyC33IveNJw0t_l6tLcGXPlpPJfit6_s'
TELEGRAM_CHAT_ID = '1933971487'

# Biến toàn cục để lưu ID của bản ghi cuối cùng đã gửi
last_sent_id = None

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

async def send_vehicle_data():
    global last_sent_id
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    conn, ssh_tunnel = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                vi.id,
                vi.capture_time,
                vi.speed,
                vi.image_data,
                lp.license_plate,
                lp.image_license_data
            FROM vehicle_images vi
            LEFT JOIN license_plates lp ON vi.capture_time = lp.capture_time
            ORDER BY vi.capture_time DESC
            LIMIT 1
        """)
        
        vehicle = cursor.fetchone()
        
        if vehicle and (last_sent_id is None or vehicle['id'] != last_sent_id):
            # Tạo message text
            message = f"""
🚗 Phát hiện xe mới!
⏰ Thời gian: {vehicle['capture_time'].strftime('%Y-%m-%d %H:%M:%S')}
🏃 Tốc độ: {vehicle['speed']} km/h
🔢 Biển số: {vehicle['license_plate'] if vehicle['license_plate'] else 'Không nhận diện được'}
"""
            # Gửi text message
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            
            # Gửi ảnh xe
            if vehicle['image_data']:
                image_binary = base64.b64decode(vehicle['image_data'])
                image_io = io.BytesIO(image_binary)
                image_io.seek(0)
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=image_io,
                    caption="Ảnh xe"
                )
            
            # Gửi ảnh biển số
            if vehicle['image_license_data']:
                license_binary = base64.b64decode(vehicle['image_license_data'])
                license_io = io.BytesIO(license_binary)
                license_io.seek(0)
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=license_io,
                    caption="Ảnh biển số"
                )
            
            # Cập nhật ID đã gửi
            last_sent_id = vehicle['id']
            print(f"Đã gửi thông tin xe mới, ID: {last_sent_id}")
                
    except Exception as e:
        print(f"Lỗi: {e}")
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"❌ Có lỗi xảy ra: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()
        ssh_tunnel.stop()

async def main():
    while True:
        await send_vehicle_data()
        await asyncio.sleep(1)  # Kiểm tra mỗi giây

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
