from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime

app = FastAPI()

# Biến toàn cục để bật/tắt chụp ảnh
capture_enabled = False

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

    # Trích xuất tên client từ tên file (ví dụ: DESKTOP-XYZ_timestamp.jpg)
    original_name = file.filename
    if "_" in original_name:
        client_name = original_name.split("_")[0]
    else:
        client_name = "unknown"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"

    # Tạo thư mục uploads/client_name/
    client_dir = os.path.join("uploads", client_name)
    os.makedirs(client_dir, exist_ok=True)

    filepath = os.path.join(client_dir, filename)

    # Ghi file
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return JSONResponse(content={"message": f"✅ Ảnh lưu tại {client_name}/{filename}"})
