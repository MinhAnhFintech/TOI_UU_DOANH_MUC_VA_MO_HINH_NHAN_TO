from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.common import APIResponse
from app.schemas.jobs import JobStatus
from app.core.database import get_db
from app.db.models import Job

router = APIRouter()

@router.get("/{job_id}", response_model=APIResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Job).where(Job.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return APIResponse(data={
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "run_id": job.run_id,
        "error": job.error
    })
