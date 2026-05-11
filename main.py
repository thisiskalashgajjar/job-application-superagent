#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main.py
Created and coded by Kalash Tejendra Gajjar.
Copyrights to Kalash Tejendra Gajjar

"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_job_agent
from database import init_db, get_all_applications, update_status

app = FastAPI(title="Job Application SuperAgent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

class JobSearchRequest(BaseModel):
    interests: list[str]
    location: str
    resume_text: str

@app.post("/search-and-apply")
def search_and_apply(req: JobSearchRequest):
    try:
        print(f"[main] Received request - Interests: {req.interests}, Location: {req.location}")
        print(f"[main] Resume length: {len(req.resume_text)} characters")
        results = run_job_agent(req.interests, req.location, req.resume_text)
        print(f"[main] Agent done - {len(results)} jobs processed")
        return {"status": "done", "jobs_processed": len(results), "jobs": results}
    except Exception as e:
        print(f"[main] ERROR: {e}")
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/applications")
def get_applications():
    return get_all_applications()

@app.patch("/applications/{app_id}/status")
def patch_status(app_id: int, payload: dict):
    update_status(app_id, payload.get("status", "Applied"))
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "running"}

if __name__ == "__main__":
    import threading
    thread = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": "0.0.0.0", "port": 8002, "reload": False},
        daemon=True
    )
    thread.start()
    print("✅ Server started at http://localhost:8000")
    print("📄 API docs at http://localhost:8000/docs")
    thread.join()
