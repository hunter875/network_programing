đây là bài của nhóm 11 môn mạng máy tính: 

# 🖼️ Auto Screenshot Sender via Mouse Click

Một ứng dụng đơn giản gồm 2 phần **Client - Server**:

- **Client**: Theo dõi sự kiện click chuột, tự động chụp màn hình và gửi ảnh về server.
- **Server**: Nhận ảnh, lưu trữ và điều khiển bật/tắt chức năng từ xa.

---

## 🧩 Tính năng

- 🖱️ Tự động chụp ảnh khi click chuột.
- ⚠️ Tránh gửi ảnh trùng (khi double click).
- ⏱️ Giới hạn tần suất gửi ảnh (chống spam).
- 🔁 Server có thể **bật/tắt chức năng gửi ảnh từ xa**.
- 💾 Ảnh được lưu theo timestamp tại thư mục `uploads/`.

---

## 🚀 Cài đặt

### 📌 Yêu cầu:

- Python 3.8+
- `pip install -r requirements.txt`

### 🗂️ Cài đặt thư viện:

```bash
pip install fastapi uvicorn requests pynput pyautogui


1. Chạy server:
uvicorn server:app --reload
2. Chạy client:
python client.py

🔧 Bật/Tắt tính năng chụp từ server
bật:
curl -X POST -H "Content-Type: application/json" -d "{\"enabled\": true}" http://127.0.0.1:8000/toggle

 Tắt:
curl -X POST -H "Content-Type: application/json" -d "{\"enabled\": false}" http://127.0.0.1:8000/toggle

