import base64
import json
import logging
import os
import time

import httpx
from fastapi import FastAPI, Request, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESEARCH_API_URL = os.environ["RESEARCH_API_URL"]

app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/push")
async def handle_push(request: Request):
    envelope = await request.json()

    message = envelope.get("message", {})
    message_id = message.get("messageId", "unknown")
    attempt = envelope.get("deliveryAttempt", 1)
    raw = message.get("data")

    if not raw:
        logger.warning("message %s has no data field, dropping", message_id)
        return Response(status_code=204)

    try:
        payload = json.loads(base64.b64decode(raw).decode("utf-8"))
    except Exception as e:
        logger.error(
            "message %s could not be decoded (%s), dropping",
            message_id, type(e).__name__
        )
        return Response(status_code=204)

    logger.info(
        "START message_id=%s attempt=%s topic=%r",
        message_id, attempt, payload.get("topic")
    )

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{RESEARCH_API_URL}/research", json=payload)
            response.raise_for_status()
            result = response.json()
    except Exception as e:
        elapsed = time.monotonic() - start
        logger.error(
            "FAILED message_id=%s attempt=%s after %.1fs (%s)",
            message_id, attempt, elapsed, type(e).__name__
        )
        return Response(status_code=500)

    elapsed = time.monotonic() - start
    logger.info(
        "DONE message_id=%s attempt=%s in %.1fs report_chars=%s sources=%s",
        message_id, attempt, elapsed,
        len(result.get("report", "")), len(result.get("urls", []))
    )

    return Response(status_code=204)
