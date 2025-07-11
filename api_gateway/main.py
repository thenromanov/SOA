import uvicorn
from fastapi import FastAPI
from routes.user_routes import router as user_router
from routes.post_routes import router as post_router
from routes.stats_routes import router as stats_router

app = FastAPI(
    title="System API Gateway", description="API Gateway for auth system", version="1.0.0"
)

app.include_router(user_router, prefix="/auth", tags=["users"])
app.include_router(post_router, prefix="/posts", tags=["posts"])
app.include_router(stats_router, prefix="/stats", tags=["stats"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "API Gateway"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
