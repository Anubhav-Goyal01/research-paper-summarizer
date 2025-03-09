from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging
import uuid
import os
from typing import Dict, Any

from app.core.paper_analyzer import PaperAnalyzer
from app.models.schemas import PaperAnalysisResponse, ErrorResponse

router = APIRouter()

analysis_cache: Dict[str, Dict[str, Any]] = {}

@router.post("/analyze", 
             response_model=Dict[str, Any],
             responses={
                 200: {"description": "Analysis job started successfully"},
                 400: {"model": ErrorResponse, "description": "Bad request"},
                 415: {"model": ErrorResponse, "description": "Unsupported file type"}
             })
async def analyze_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    paper_analyzer: PaperAnalyzer = Depends(lambda: PaperAnalyzer())
):
    """
    Endpoint to submit a research paper for analysis.
    Returns a job ID immediately and processes the paper in the background.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=415,
            detail="Only PDF files are supported."
        )
    
    job_id = str(uuid.uuid4())
    
    analysis_cache[job_id] = {
        "status": "processing",
        "filename": file.filename,
        "result": None
    }
    
    file_content = await file.read()
    
    async def process_paper(job_id: str, filename: str, file_content: bytes):
        try:
            temp_file_path = await paper_analyzer.save_upload_file(file_content)
            
            result = await paper_analyzer.analyze_paper(temp_file_path)
            
            analysis_cache[job_id]["status"] = "completed"
            analysis_cache[job_id]["result"] = result
            
        except Exception as e:
            logging.error(f"Error processing paper: {str(e)}")
            analysis_cache[job_id]["status"] = "failed"
            analysis_cache[job_id]["error"] = str(e)
    
    background_tasks.add_task(process_paper, job_id, file.filename, file_content)
    
    return {"job_id": job_id, "status": "processing"}

@router.get("/status/{job_id}", 
            response_model=Dict[str, Any],
            responses={
                404: {"model": ErrorResponse, "description": "Job not found"}
            })
async def get_job_status(job_id: str):
    """
    Check the status of a paper analysis job.
    If the job is complete, returns the analysis results.
    """
    if job_id not in analysis_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Job ID {job_id} not found"
        )
    
    job_info = analysis_cache[job_id]
    
    if job_info["status"] == "completed":
        return {
            "status": "completed",
            "filename": job_info["filename"],
            "result": job_info["result"]
        }
    elif job_info["status"] == "failed":
        return {
            "status": "failed",
            "filename": job_info["filename"],
            "error": job_info.get("error", "Unknown error")
        }
    else:
        return {
            "status": "processing",
            "filename": job_info["filename"]
        }

@router.delete("/jobs/{job_id}", 
               responses={
                   200: {"description": "Job deleted successfully"},
                   404: {"model": ErrorResponse, "description": "Job not found"}
               })
async def delete_job(job_id: str):
    """
    Delete a job and its results from the cache.
    """
    if job_id not in analysis_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Job ID {job_id} not found"
        )
    
    del analysis_cache[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}
