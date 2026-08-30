import os

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update
from telegram.ext import CallbackContext

from bot.config import BOT_TOKEN
from bot.handlers.income import send_monthly_income_reminders
from bot.main import create_application


app = FastAPI()
application = create_application()

MONTHLY_JOB_SECRET = os.environ["MONTHLY_JOB_SECRET"]
TELEGRAM_WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]


@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()


@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.post("/telegram-webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    update = Update.de_json(data, application.bot)

    await application.process_update(update)
    return {"ok": True}


@app.post("/monthly-job")
async def monthly_job(
    x_job_secret: str | None = Header(default=None),
):
    if x_job_secret != MONTHLY_JOB_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    context = CallbackContext(application)

    await send_monthly_income_reminders(context)
    return {"ok": True}