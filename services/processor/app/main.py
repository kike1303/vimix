from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import jobs, processors

app = FastAPI(
    title="Vimix – Processor API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4321"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(processors.router)
app.include_router(jobs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
