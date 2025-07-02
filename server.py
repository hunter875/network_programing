import argparse
from typing import Dict
from fastapi import FastAPI, UploadFile, File, Path
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor
import asyncio
import hashlib
import uvicorn
import requests
from contextlib import asynccontextmanager

banner = """
╔══════════════════════════════════════════════════════════╗
║            📸 SCREEN MONITORING SERVER - FASTAPI         ║
║----------------------------------------------------------║
║ 🔐 Mã hóa ảnh bằng Fernet (AES128 + HMAC)                ║
║ 📁 Lưu ảnh theo client trong thư mục /uploads            ║
║ 📡 POST /uploadfile/   → gửi ảnh                         ║
║ ✅ POST --up/down      → bật/tắt chức năng               ║
║ 🔍 GET /status         → kiểm tra trạng thái             ║
║ 🧮 GET /last_image_hash/{client}                         ║
║ 👥 GET /clients        → xem danh sách client            ║
╚══════════════════════════════════════════════════════════╝
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(banner)
    yield

app = FastAPI(lifespan=lifespan)

# Biến toàn cục
capture_enabled = False
client_last_seen: Dict[str, str] = {}
client_last_hash: Dict[str, str] = {}

# Khóa mã hóa dùng chung
SECRET_KEY = b'Qw8v1Qw2Qw8v1Qw2Qw8v1Qw2Qw8v1Qw2Qw8v1Qw2Qw8='
fernet = Fernet(SECRET_KEY)
executor = ThreadPoolExecutor(max_workers=4)

class ToggleRequest(BaseModel):
    enabled: bool

@app.post("/toggle")
async def toggle_capture(req: ToggleRequest):
    global capture_enabled
    capture_enabled = req.enabled
    return {"capture_enabled": capture_enabled}

@app.get("/status")
async def get_status():
    return {"enabled": capture_enabled}

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not capture_enabled:
        return JSONResponse(content={"message": "❌ Chức năng chụp đang tắt"}, status_code=403)

    original_name = file.filename
    client_name = original_name.split("_")[0] if "_" in original_name else "unknown"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    client_dir = os.path.join("uploads", client_name)
    os.makedirs(client_dir, exist_ok=True)
    filepath = os.path.join(client_dir, filename)
    file_bytes = await file.read()

    def process_and_save():
        nonlocal file_bytes
        try:
            file_bytes_dec = fernet.decrypt(file_bytes) if original_name.endswith('.enc') else file_bytes
        except Exception:
            return False

        md5_hash = hashlib.md5(file_bytes_dec).hexdigest()
        with open(filepath, "wb") as f:
            f.write(file_bytes_dec)
        client_last_hash[client_name] = md5_hash
        return True

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, process_and_save)

    if not result:
        return JSONResponse(content={"message": "❌ Giải mã thất bại"}, status_code=400)

    client_last_seen[client_name] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return JSONResponse(content={"message": f"✅ Ảnh lưu tại {client_name}/{filename}"})


@app.get("/last_image_hash/{client_name}")
async def get_last_image_hash(client_name: str = Path(..., description="Tên client")):
    hash_val = client_last_hash.get(client_name)
    if hash_val:
        return {"client": client_name, "last_image_md5": hash_val}
    else:
        return JSONResponse(content={"message": "Client chưa gửi ảnh hoặc không tồn tại"}, status_code=404)

@app.get("/clients")
async def get_clients():
    return {"clients": client_last_seen}


# ✅ Hàm chính có hỗ trợ --up / --down
def main():
    parser = argparse.ArgumentParser(
        description="📸 FastAPI Screen Monitor Server - Nhận ảnh từ client qua HTTP.\n"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Địa chỉ host (mặc định: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Cổng chạy server (mặc định: 8000)")
    parser.add_argument("--ssl", action="store_true", help="Chạy server HTTPS nếu có cert.pem và key.pem")
    parser.add_argument("--up", action="store_true", help="Gửi yêu cầu bật server (toggle ON)")
    parser.add_argument("--down", action="store_true", help="Gửi yêu cầu tắt server (toggle OFF)")

    args = parser.parse_args()

    if args.up:
        try:
            r = requests.post(f"http://{args.host}:{args.port}/toggle", json={"enabled": True})
            print("✅ Đã gửi yêu cầu BẬT server:", r.json())
        except Exception as e:
            print("❌ Không gửi được yêu cầu BẬT:", e)
        return

    if args.down:
        try:
            r = requests.post(f"http://{args.host}:{args.port}/toggle", json={"enabled": False})
            print("✅ Đã gửi yêu cầu TẮT server:", r.json())
        except Exception as e:
            print("❌ Không gửi được yêu cầu TẮT:", e)
        return

    # Nếu không phải toggle thì khởi động server
    if args.ssl:
        uvicorn.run("server:app", host=args.host, port=args.port,
                    ssl_keyfile="key.pem", ssl_certfile="cert.pem", reload=True)
    else:
        uvicorn.run("server:app", host=args.host, port=args.port, reload=True)

if __name__ == "__main__":
    main()