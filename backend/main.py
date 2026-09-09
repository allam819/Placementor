from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

from app.api import router as api_router

def create_app() -> FastAPI:
    app = FastAPI(title="Placement Platform API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    app.include_router(api_router, prefix="/api")

    return app

app = create_app()
