"""
Job Status Store - In-memory store for tracking pipeline progress.
"""

from typing import Dict, Any, Optional
import asyncio

# In-memory store: job_id -> status_dict
# In production, use Redis for persistence
_job_store: Dict[str, Dict[str, Any]] = {}
_job_locks: Dict[str, asyncio.Lock] = {}

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return _job_store.get(job_id)

async def update_job_status(job_id: str, status_update: Dict[str, Any]):
    if job_id not in _job_locks:
        _job_locks[job_id] = asyncio.Lock()
    
    async with _job_locks[job_id]:
        if job_id not in _job_store:
            _job_store[job_id] = {}
        _job_store[job_id].update(status_update)

def initialize_job(job_id: str, total_businesses: int):
    _job_store[job_id] = {
        "job_id": job_id,
        "status": "running",
        "total_businesses": total_businesses,
        "processed": 0,
        "progress": 0,
        "scraper_done": 0,
        "analyzer_done": 0,
        "outreach_done": 0,
        "agents": {
            "discovery": {"status": "completed", "progress": 100},
            "scraper": {"status": "pending", "progress": 0},
            "analyzer": {"status": "pending", "progress": 0},
            "outreach": {"status": "pending", "progress": 0},
        }
    }

async def start_job_step(job_id: str, agent_name: str):
    """Marks an agent step as running if it's currently pending."""
    if job_id not in _job_locks:
        _job_locks[job_id] = asyncio.Lock()
    async with _job_locks[job_id]:
        if job_id in _job_store:
            job = _job_store[job_id]
            if agent_name in job["agents"] and job["agents"][agent_name]["status"] == "pending":
                job["agents"][agent_name]["status"] = "running"

async def complete_job_step(job_id: str, counter_name: str, agent_name: str):
    """Increments a step's done counter and updates agent status in a thread-safe manner."""
    if job_id not in _job_locks:
        _job_locks[job_id] = asyncio.Lock()
    async with _job_locks[job_id]:
        if job_id in _job_store:
            job = _job_store[job_id]
            job[counter_name] = job.get(counter_name, 0) + 1
            done = job[counter_name]
            total = job["total_businesses"]
            
            status_val = "completed" if done == total else "running"
            progress_val = 100 if done == total else int((done / total) * 100)
            job["agents"][agent_name] = {"status": status_val, "progress": progress_val}
            
            # Cascade running state to next logical agent
            if status_val == "completed":
                if agent_name == "scraper" and job["agents"]["analyzer"]["status"] == "pending":
                    job["agents"]["analyzer"]["status"] = "running"
                elif agent_name == "analyzer" and job["agents"]["outreach"]["status"] == "pending":
                    job["agents"]["outreach"]["status"] = "running"

