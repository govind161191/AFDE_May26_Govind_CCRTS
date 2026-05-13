from fastapi import FastAPI
from database import engine, Base
import models  # noqa
Base.metadata.create_all(bind=engine)
app = FastAPI(title="CCRTS API", version="0.1.0")

@app.get("/")
def root():
    return {"service": "CCRTS API", "status": "ok"}
