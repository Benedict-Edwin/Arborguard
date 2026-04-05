import os
import shutil
import uuid
import json
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from video_processor import VideoProcessor

app = FastAPI(title="Tree & Powerline Anomaly Detection")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOADS_DIR = "uploads"
OUTPUT_DIR = "output"
SNAPSHOTS_DIR = "snapshots"
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# Static files for snapshots and results
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
app.mount("/snapshots", StaticFiles(directory=SNAPSHOTS_DIR), name="snapshots")

# In-memory job status tracker
jobs = {}

@app.get("/")
async def root():
    return {"message": "Welcome to the Tree & Powerline Anomaly Detection API"}

@app.post("/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{file.filename}"
    file_path = os.path.join(UPLOADS_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    jobs[job_id] = {"status": "processing", "progress": 0}
    
    # Start background processing
    background_tasks.add_task(process_job, job_id, file_path)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

def process_job(job_id: str, file_path: str):
    try:
        processor = VideoProcessor(output_dir=OUTPUT_DIR, snapshot_dir=SNAPSHOTS_DIR)
        output_path, log_path, logs = processor.process_video(file_path)
        
        # Count high risk events
        high_risk_count = sum(1 for entry in logs for anomaly in entry.get('anomalies', []) if anomaly.get('risk') == "HIGH")
        
        jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "output_video": f"/output/{os.path.basename(output_path)}",
            "logs": logs,
            "high_risk_count": high_risk_count
        }
    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
