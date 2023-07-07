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
    while True:

      if await request.is_disconnected():
        break

      for new_text in streamer:
        yield {"text": new_text}

      await asyncio.sleep(MESSAGE_STREAM_DELAY)

  return EventSourceResponse(event_generator())


if __name__ == "__main__":
  load_model()
  uvicorn.run(app, host="127.0.0.1", port=8000)
