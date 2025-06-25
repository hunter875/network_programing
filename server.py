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

app = FastAPI()

# Biến toàn cục để bật/tắt chụp ảnh
capture_enabled = False

# Biến toàn cục lưu thời điểm cuối mỗi client gửi ảnh
client_last_seen: Dict[str, str] = {}

# Thêm biến lưu hash MD5 cuối cùng của mỗi client
client_last_hash: Dict[str, str] = {}

# Khóa bí mật (dùng chung với client)
SECRET_KEY = b'Qw8v1Qw2Qw8v1Qw2Qw8v1Qw2Qw8v1Qw2Qw8v1Qw2Qw8='  # 32 bytes base64
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
    if "_" in original_name:
        client_name = original_name.split("_")[0]
    else:
        client_name = "unknown"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    client_dir = os.path.join("uploads", client_name)
    os.makedirs(client_dir, exist_ok=True)
    filepath = os.path.join(client_dir, filename)
    file_bytes = await file.read()

    def process_and_save():
        nonlocal file_bytes
        # Nếu là file mã hóa, giải mã trước khi lưu
        if original_name.endswith('.enc'):
            try:
                file_bytes_dec = fernet.decrypt(file_bytes)
            except Exception:
                return False
        else:
            file_bytes_dec = file_bytes
        # Tính hash MD5
        md5_hash = hashlib.md5(file_bytes_dec).hexdigest()
        # Lưu file
        with open(filepath, "wb") as f:
            f.write(file_bytes_dec)
        # Lưu hash MD5 cuối cùng
        client_last_hash[client_name] = md5_hash
        return True

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, process_and_save)
    if not result:
        return JSONResponse(content={"message": "❌ Giải mã thất bại"}, status_code=400)
    
    # Cập nhật thời điểm cuối client gửi ảnh
    client_last_seen[client_name] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return JSONResponse(content={"message": f"✅ Ảnh lưu tại {client_name}/{filename}"})

@app.get("/last_image_hash/{client_name}")
async def get_last_image_hash(client_name: str = Path(..., description="Tên client")):
    """
    Trả về hash MD5 của ảnh cuối cùng client đã gửi lên.
    """
    hash_val = client_last_hash.get(client_name)
    if hash_val:
        return {"client": client_name, "last_image_md5": hash_val}
    else:
        return JSONResponse(content={"message": "Client chưa gửi ảnh hoặc không tồn tại"}, status_code=404)

@app.get("/clients")
async def get_clients():
    """
    Trả về danh sách các client đã gửi ảnh lên gần đây và thời điểm cuối cùng.
    """
    return {"clients": client_last_seen}
