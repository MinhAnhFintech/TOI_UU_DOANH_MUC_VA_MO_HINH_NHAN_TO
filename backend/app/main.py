
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, get_logger

logger = get_logger(stage="startup")

app = FastAPI(title="VN30 Factor Optimizer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import data, factors, regression, portfolio, backtest, jobs, export

@app.on_event("startup")
async def startup_event():
    setup_logging()
    logger.info("Starting VN30 Factor Optimizer API")

app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(factors.router, prefix="/api/v1/factors", tags=["factors"])
app.include_router(regression.router, prefix="/api/v1/regression", tags=["regression"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(backtest.router, prefix="/api/v1/backtest", tags=["backtest"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
