from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from celery.result import AsyncResult

from langchain_pipeline.run_pipeline import run_chain

router = APIRouter()

class FormData(BaseModel):
    website_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    prompt: str

@router.post("/submit-task")
async def submit_form(data: FormData):
    if not (data.website_url or data.github_url):
        raise HTTPException(status_code=400, detail="At least one source is required.")
    
    source = None
    scan_type = None
    
    if data.website_url and data.github_url:
        source = [str(data.website_url), str(data.github_url)]
        scan_type = ["web", "code"]
    elif data.website_url:
        source = [str(data.website_url)]
        scan_type = ["web"]
    elif data.github_url:
        source = [str(data.github_url)]
        scan_type = ["code"]
    
    payload = {
        "source": source,
        "scan_type": scan_type,
        "prompt": data.prompt
    }
    
    try:
        task = run_chain.delay(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during processing: {str(e)}")
    
    return {"task_id": task.id, "message": "Report Generation Initiated", "status": "pending"}


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    result = AsyncResult(task_id)
    return {
        "status": result.status,
        "result": result.result if result.ready() else None
    }
