import subprocess
import threading
from bardapi import Bard
from usecase.bard import getAddressByKey, getArticleByKeyAndField, getArticlesSentimentByKey, isArticlesEmpty, summarize, summarize_by_city
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from util.city_translation import city_code

app = FastAPI()

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/summary')
async def bard_route(request: Request):
  body = await request.json()
  key = body["key"]
  topic = body["topic"]

  articles = {
      "positive": getArticleByKeyAndField(key, "PositiveNews"),
      "negative": getArticleByKeyAndField(key, "NegativeNews"),
      "popularity": getArticleByKeyAndField(key, "PopularityNews")
  }
  if isArticlesEmpty(articles):
    return {"summary": "目前無相關討論" , "address": []}

  sentiment_count = getArticlesSentimentByKey(key)
  addresses = getAddressByKey(key)

  summaries = {}
  for word_count in [60, 90, 150]:
    summary = summarize(topic, articles, sentiment_count, addresses, word_count)

    if ("語言模型" in summary and "我" in summary) or ("文字型人工智慧" in summary and "我" in summary):
      summary = "目前無相關討論"

    summary = f"""
    **正負向討論數量:**
    正向: {sentiment_count['positive_count']} | 負向: {sentiment_count["negative_count"]}
    {summary}
    """.strip()
    summaries[word_count] = summary
  return {"summaries": summaries, "address": addresses}

@app.post('/summary/{address}')
async def bard_address_route(address: str, request: Request):
  body = await request.json()
  key = body["key"]
  topic = body["topic"]
  word_count = body["wordCount"]

  articles = {
      "positive": getArticleByKeyAndField(key, "PositiveNews"),
      "negative": getArticleByKeyAndField(key, "NegativeNews"),
      "popularity": getArticleByKeyAndField(key, "PopularityNews")
  }
  if isArticlesEmpty(articles):
    return {"summary": "目前無相關討論"}
  sentiment_count = getArticlesSentimentByKey(key)
  city = city_code.get(int(address), "未知地區")

  summaries = {}
  for word_count in [60, 90, 150]:
    summary = summarize_by_city(topic, articles, sentiment_count, city, word_count)
    
    if ("語言模型" in summary and "我" in summary) or ("文字型人工智慧" in summary and "我" in summary):
      summary = "目前無相關討論"

    summary = f"""
    地區: {city} \n
    {summary}
    """.strip()
    summaries[word_count] = summary

  return {"summaries": summaries}

def run_server():
  uvicorn.run(app, host="127.0.0.1", port=8000)

def run_ngrok():
  subprocess.run("./start.sh", shell=True)

if __name__ == "__main__":
  uvicorn_thread = threading.Thread(target=run_server)
  ngrok_thread = threading.Thread(target=run_ngrok)

  # ngrok_thread.start()
  
  uvicorn_thread.start()

  uvicorn_thread.join()
  # ngrok_thread.join()