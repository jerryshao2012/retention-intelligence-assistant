from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.api.routes import router
from app.core.config import EVAL_BATCH_WINDOW_MINUTES
from app.db import init_db
from app.evaluations.batch import run_eval_batch

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(run_eval_batch, "interval", minutes=EVAL_BATCH_WINDOW_MINUTES, id="eval_batch")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Retention Intelligence Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
