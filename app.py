import asyncio
import uvicorn
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from usecase import vicuna, gpt

MESSAGE_STREAM_DELAY = 1
MESSAGE_STREAM_RETRY_TIMEOUT = 15000

app = FastAPI()
vicuna.load_model()

@app.post("/summary/gpt")
async def gpt_route(request: Request):
  body = await request.json()
  content = body["content"]
  result = gpt.summarize(content)
  return {"data": result}

@app.post('/summary')
async def vicuna_route(request: Request):
  body = await request.json()
  streamer = vicuna.summarize(body["content"])

  async def event_generator():
    for new_text in streamer:
      yield {"data": new_text}

  return EventSourceResponse(event_generator())


if __name__ == "__main__":
  uvicorn.run(app, host="127.0.0.1", port=8000)
