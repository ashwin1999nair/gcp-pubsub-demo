import base64
import json
import logging

from fastapi import FastAPI, Request, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        "RECEIVED message_id=%s attempt=%s topic=%r n_urls=%s",
        message_id, attempt, payload.get("topic"), payload.get("n_urls")
    )

    return Response(status_code=204)
