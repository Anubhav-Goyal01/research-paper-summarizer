#!/usr/bin/env python
"""
Entry point script for running the Research Paper Summarizer FastAPI application.
This script is used by VS Code's debugger to launch the application.
"""
import sys
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Run the FastAPI application with uvicorn."""
    logger.info(f"Starting server with Python: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    
    # Run the application with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
