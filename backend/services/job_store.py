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
        "agents": {
            "discovery": {"status": "completed", "progress": 100},
            "scraper": {"status": "pending", "progress": 0},
            "analyzer": {"status": "pending", "progress": 0},
            "outreach": {"status": "pending", "progress": 0},
        }
    }
