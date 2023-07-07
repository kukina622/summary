import asyncio
import uvicorn
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from usecase.summary import load_model, summarize

MESSAGE_STREAM_DELAY = 1
MESSAGE_STREAM_RETRY_TIMEOUT = 15000

app = FastAPI()


@app.post('/summary')
async def summary_route(request: Request):
  body = await request.json()
  streamer = summarize(body["content"])

  async def event_generator():
    for new_text in streamer:
      yield {"data": new_text}

  return EventSourceResponse(event_generator())


if __name__ == "__main__":
  load_model()
  uvicorn.run(app, host="127.0.0.1", port=8000)
