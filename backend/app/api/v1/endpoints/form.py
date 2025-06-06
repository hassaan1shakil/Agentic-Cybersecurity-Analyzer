# backend/app/api/form.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal
import subprocess
import uuid
from datetime import datetime
import os

router = APIRouter()

class FormData(BaseModel):
    website_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    local_path: Optional[str] = None
    prompt: str
    scan_type: Literal["web", "code", "both"] = "both"  # Add scan type

@router.post("/submit-form")
async def submit_form(data: FormData):
    if not (data.website_url or data.github_url or data.local_path):
        raise HTTPException(status_code=400, detail="At least one source is required.")
    
    # Determine single source with precedence: website > local files > github
    source = None
    scan_type = None
    if data.website_url:
        source = str(data.website_url)
        scan_type = "web"
    elif data.local_path:
        source = str(data.local_path)
        scan_type = "code"
    elif data.github_url:
        source = str(data.github_url)
        scan_type = "code"
    
    # Create unique token
    process_token = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_token = f"{timestamp}_{process_token}"
    
    # Choose scanner script based on determined scan type
    scanner_script = "./scripts/run_scanner.py"
    
    command = [
        "python3",
        scanner_script,
        "--source", source,
        "--token", unique_token,
        "--scan-type", scan_type,
    ]

    if data.prompt:
        command.extend(["--prompt", data.prompt])

    # Add appropriate source type flag
    if scan_type == "web":
        command.append("--is-web")
    elif scan_type == "code":
        if data.local_path:
            command.append("--is-local")
        else:
            command.append("--is-github")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            env={**os.environ, "SCAN_TOKEN": unique_token}
        )
        
        process_id = process.pid

        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": f"Started {scan_type} scan in background",
                "data": {
                    "process_id": process_id,
                    "token": unique_token,
                    "scan_type": scan_type,
                    "source_used": source,
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scan process: {str(e)}"
        )
        
@router.get("/process-status/{token}")
async def get_process_status(token: str):
    # Here you would implement logic to check the status of the process
    # You might want to store process information in a database or file
    # For now, we'll just check if the process is running
    try:
        process_id = int(token.split('_')[2])  # Extract PID from token
        subprocess.check_call(['ps', '-p', str(process_id)])
        return {"status": "running", "token": token}
    except subprocess.CalledProcessError:
        return {"status": "completed", "token": token}
    except Exception as e:
        return {"status": "error", "message": str(e)}