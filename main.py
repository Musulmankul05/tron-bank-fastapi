from fastapi import FastAPI
from router import users
import uvicorn

app = FastAPI(title="root")
app.include_router(users.router, prefix="/api/v1")

@app.get("/api/v1", summary="main", tags=["ROOT"])
async def root():
    return {"message": "you're in the root"}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)