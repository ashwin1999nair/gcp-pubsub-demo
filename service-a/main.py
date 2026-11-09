import json
import os

from fastapi import FastAPI
from google.cloud import pubsub_v1
from pydantic import BaseModel, Field

PROJECT_ID=os.environ["PROJECT_ID"]
TOPIC_ID=os.environ.get("TOPIC_ID", "research-jobs")

app=FastAPI()
publisher=pubsub_v1.PublisherClient()
topic_path=publisher.topic_path(PROJECT_ID,TOPIC_ID)

class JobRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=200)
    n_urls: int = Field(default=5, ge=1, le=10)

@app.get("/")
def health():
    return {"status", "ok"}

@app.post("/jobs", status_code=202)
def submit(req: JobRequest):
    payload = json.dumps({"topic": req.topic, "n_urls": req.n_urls}).encode("utf-8")
    future=publisher.publish(topic_path, payload)
    message_id=future.result(timeout=10)
    return {"status": "accepted", "message_id": message_id}