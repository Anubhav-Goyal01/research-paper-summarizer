from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging
import uuid
import os
from typing import Dict, Any

from app.core.paper_analyzer import PaperAnalyzer
from app.core.chat_manager import ChatManager
from app.clients.gemini_ai import GeminiClient
from app.models.schemas import ErrorResponse, ChatRequest

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


@router.post("/jobs/{job_id}/chat", 
             response_model=Dict[str, Any],
             responses={
                 200: {"description": "Chat response"},
                 404: {"model": ErrorResponse, "description": "Job not found"},
                 400: {"model": ErrorResponse, "description": "Bad request"}
             })
async def chat_with_paper(job_id: str, chat_request: ChatRequest):
    """
    Chat with an AI about a previously analyzed paper.
    
    Args:
        job_id: The ID of the analysis job
        chat_request: The chat request containing the user's message
        
    Returns:
        Dictionary containing the response and updated chat history
    """
    if job_id not in analysis_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Job ID {job_id} not found"
        )
    
    job_info = analysis_cache[job_id]
    
    if job_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not completed yet"
        )
    
    if "result" not in job_info or not job_info["result"]:
        raise HTTPException(
            status_code=400,
            detail=f"No analysis result found for job {job_id}"
        )
    
    if "chat_history" not in job_info:
        job_info["chat_history"] = []
    
    chat_manager = ChatManager(GeminiClient())
    
    try:
        chat_result = await chat_manager.process_chat_message(
            job_id=job_id,
            user_message=chat_request.message,
            analysis_result=job_info["result"],
            chat_history=job_info["chat_history"]
        )
        
        job_info["chat_history"] = chat_result["updated_history"]
        
        return {
            "response": chat_result["response"],
            "job_id": job_id
        }
    except Exception as e:
        logging.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/jobs/{job_id}/chat", 
            response_model=Dict[str, Any],
            responses={
                200: {"description": "Chat history"},
                404: {"model": ErrorResponse, "description": "Job not found"}
            })
async def get_chat_history(job_id: str):
    """
    Get the chat history for a specific job.
    
    Args:
        job_id: The ID of the analysis job
        
    Returns:
        Dictionary containing the chat history
    """
    if job_id not in analysis_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Job ID {job_id} not found"
        )
    
    job_info = analysis_cache[job_id]
    
    chat_history = job_info.get("chat_history", [])
    
    return {
        "job_id": job_id,
        "chat_history": chat_history
    }
