import requests
import time
import hashlib
import io
import pyautogui
import socket
from pynput import mouse

# --- Cấu hình ---
SERVER_UPLOAD_URL = "http://127.0.0.1:8000/uploadfile/"
SERVER_STATUS_URL = "http://127.0.0.1:8000/status"
DEBOUNCE_SECONDS = 0.5

# --- Biến toàn cục ---
last_sent_time = 0
last_image_hash = None
hostname = socket.gethostname()


def is_capture_enabled():
    try:
        response = requests.get(SERVER_STATUS_URL)
        return response.json().get("enabled", False)
    except Exception as e:
        print(f"⚠️ Không kiểm tra được trạng thái server: {e}")
        return False


def capture_screenshot_bytes():
    screenshot = pyautogui.screenshot()
    byte_io = io.BytesIO()
    screenshot.save(byte_io, format="JPEG", quality=95)
    return byte_io.getvalue()


def get_hash(data: bytes):
    return hashlib.md5(data).hexdigest()


def send_screenshot_if_valid():
    global last_sent_time, last_image_hash

    now = time.time()
    if now - last_sent_time < DEBOUNCE_SECONDS:
        print("⏳ Click quá nhanh, bỏ qua.")
        return

    if not is_capture_enabled():
        print("🚫 Server đang tắt chức năng chụp.")
        return

    img_bytes = capture_screenshot_bytes()
    current_hash = get_hash(img_bytes)

    if current_hash == last_image_hash:
        print("⚠️ Ảnh trùng, bỏ qua.")
        return

    last_image_hash = current_hash
    last_sent_time = now

    filename = f"{hostname}_screenshot.jpg"
    files = {"file": (filename, img_bytes, "image/jpeg")}

    try:
        response = requests.post(SERVER_UPLOAD_URL, files=files)
        print(f"✅ {response.json().get('message')}")
    except Exception as e:
        print(f"❌ Gửi ảnh thất bại: {e}")


def on_click(x, y, button, pressed):
    if pressed:
        print(f"🖱️ Click tại ({x}, {y})")
        send_screenshot_if_valid()


if __name__ == "__main__":
    print(f"🚀 Đang theo dõi click chuột... ({hostname})")
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
