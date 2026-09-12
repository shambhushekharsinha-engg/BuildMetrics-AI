import os
import re

api_path = "api.py"
with open(api_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add logging imports and setup
logging_setup = """import logging
from pythonjsonlogger import jsonlogger
import time
from fastapi import Request

logger = logging.getLogger("buildmetrics_api")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(logHandler)

@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    logger.info("Request started", extra={"request_id": request_id, "path": request.url.path, "method": request.method})
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    logger.info("Request completed", extra={
        "request_id": request_id, 
        "path": request.url.path, 
        "status_code": response.status_code,
        "latency_sec": round(process_time, 4)
    })
    return response
"""

# Insert logging setup after app = FastAPI()
content = content.replace('app = FastAPI(title="BuildMetrics API", version="1.0.0")', 'app = FastAPI(title="BuildMetrics API", version="1.0.0")\n' + logging_setup)

with open(api_path, "w", encoding="utf-8") as f:
    f.write(content)
