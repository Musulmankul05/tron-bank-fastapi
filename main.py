import uuid

import uvicorn
from fastapi import FastAPI, Request

from routers import cards, transactions, users

app = FastAPI(title="root")
app.include_router(users.router, prefix="/api/v1")
app.include_router(cards.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("x-request-id") or str(uuid.uuid4())

    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response


@app.get("/api/v1", summary="main", tags=["ROOT"])
async def root():
    return {"message": "you're in the root"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
