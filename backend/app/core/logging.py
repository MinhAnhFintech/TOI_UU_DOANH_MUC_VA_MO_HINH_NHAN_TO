import sys
from loguru import logger
import uuid

def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[run_id]} | {extra[stage]} | {message}",
        level="INFO",
        serialize=True,
    )
    
def get_logger(run_id: str = None, stage: str = "general"):
    if not run_id:
        run_id = str(uuid.uuid4())
    return logger.bind(run_id=run_id, stage=stage)
