from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models  # noqa
from routers import auth_router, users_router, categories_router
Base.metadata.create_all(bind=engine)
app = FastAPI(title="CCRTS API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(categories_router.router)

@app.get("/")
def root():
    return {"service": "CCRTS API", "status": "ok"}
