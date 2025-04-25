import uvicorn
from fastapi import FastAPI
from routes.user_routes import router as user_router, post_routes

app = FastAPI(
    title="System API Gateway", description="API Gateway for auth system", version="1.0.0"
)

app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(post_routes.router, prefix="/posts", tags=["posts"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "API Gateway"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
