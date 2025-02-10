import logging
from datetime import datetime

from audiobookbay import search_audiobook
from fastapi import FastAPI, Query, HTTPException
from utils import custom_logger
import uvicorn

app = FastAPI()

logger = custom_logger(__name__)

@app.get("/status")
async def status():
    now = datetime.utcnow().isoformat() + "Z"
    return {"status": "ok", "timestamp": now}

@app.get("/search")
async def search(
    query: str = Query(..., description="Search query"),
):
    """
    Searches a webpage based on the provided query and page number.
    """
    try:
        results = search_audiobook(query)
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True) 
