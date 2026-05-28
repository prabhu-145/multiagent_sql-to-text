from fastapi import FastAPI
from routes.chat_route import router as chat_router

app = FastAPI(title="Life Sciences Multi-Agent Assistant")
app.include_router(chat_router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "running", "message": "Life Sciences AI Assistant Backend"}
