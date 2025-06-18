from fastapi import FastAPI, UploadFile, File
import os, shutil
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()
os.makedirs("uploads", exist_ok=True)

capture_enabled = {"enabled": True}

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not capture_enabled["enabled"]:
        return {"message": "❌ Chức năng chụp đang tắt"}
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + file.filename
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"✅ Đã lưu ảnh: {filename}"}

class ToggleRequest(BaseModel):
    enabled: bool

@app.post("/toggle")
def toggle_capture(req: ToggleRequest):
    capture_enabled["enabled"] = req.enabled
    return {"message": f"Chức năng chụp đã {'bật' if req.enabled else 'tắt'}"}

@app.get("/status")
def get_status():
    return {"enabled": capture_enabled["enabled"]}
