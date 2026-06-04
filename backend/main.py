from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat_route import router as chat_router

app = FastAPI(
    title="Life Sciences AI Assistant Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://16.54.41.169:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "Life Sciences AI Assistant Backend"
    }