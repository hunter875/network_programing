from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor
import asyncio

app = FastAPI()

# Biến toàn cục để bật/tắt chụp ảnh
capture_enabled = False

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
        with open(filepath, "wb") as f:
            f.write(file_bytes_dec)
        return True

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, process_and_save)
    if not result:
        return JSONResponse(content={"message": "❌ Giải mã thất bại"}, status_code=400)
    return JSONResponse(content={"message": f"✅ Ảnh lưu tại {client_name}/{filename}"})
