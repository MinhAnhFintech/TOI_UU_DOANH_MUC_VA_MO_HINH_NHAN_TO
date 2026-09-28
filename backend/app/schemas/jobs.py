from pydantic import BaseModel
from typing import Optional

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    run_id: Optional[str] = None
    error: Optional[str] = None

class JobCreate(BaseModel):
    type: str
