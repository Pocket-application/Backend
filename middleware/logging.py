import time
from fastapi import Request

async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 3)

    print(f"{request.method} {request.url.path} {response.status_code} {duration}s")
    return response
