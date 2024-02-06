import configparser
import datetime
from bardapi import Bard, SESSION_HEADERS
import redis
import re
import json
import redis
import sys

sys.path.append("..")
from util.city_translation import city_translation

config = configparser.ConfigParser()
config.read('config.ini')

cache = redis.Redis(host='0.tcp.jp.ngrok.io',
                    port=int(config['redis']['port']),
                    password="!nWB!V2!yjTum")

bard = Bard(token=config['bard']['token'])

def shrink_spaces_and_newlines(text):
  url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
  text = re.sub(url_pattern, '', text)
  text = re.sub(r'　', ' ', text)
  text = re.sub(r'\s+', ' ', text)
  text = re.sub(r'\n+', '', text)

  return text

def summarize(topic: str, articles, sentiment_count, address, word_count = 150):

  instruction = """
  你是一個文章摘要生成器，將會閱讀的文章後，提供使用者文章中對主題的摘要。
  摘要內容只需且必須要列出這5點，並用粗體把標題標註。
  1. 事件經過
  2. 大眾評價看法
  3. 正負向討論點
  4. 討論熱點
  5. 結論
  正負向討論點，分為正向與負向，先一個大標正負向討論點，再分別列出正向與負向的討論點。
  不要寫補充說明、調整說明、修改說明、字數說明、日期說明等等。
  你將會獲得正向、負向與最熱門的文章，
  還有最多討論的地區前三名，以及正負向的討論數量，
  將接收到的內容，經過總結後寫摘要，
  約{word_count}字左右，專注於寫新聞的內容。
  不要寫怎麼調整，不要寫調整說明，不要把新聞的日期寫出來，不要寫什麼需要修改，不要寫修改，不要寫字數，而是專注於寫新聞的內容。
  主題: ###{topic}###
  正向文章: 
  ###
    {positive_article}
  ###
  負向文章: 
  ###
    {negative_article}
  ###
  最熱門文章: 
  ###
    {popularity_article}
  ###
  討論地區前三名: 
  ###
    1. {address_1} 2. {address_2} 3. {address_3}
  ###
  正負向討論數量: 
  ###
    正向: {positive_count} 負向: {negative_count}
  ###
  摘要: """

  articles_positive = "---\n".join(articles["positive"])[:800]
  articles_negative = "---\n".join(articles["negative"])[:800]
  articles_popularity = "---\n".join(articles["popularity"])[:800]

  prompt = instruction.format(
    word_count         = word_count,
    topic              = topic, 
    positive_article   = articles_positive   if len(articles["positive"]) > 0 else "無",
    negative_article   = articles_negative   if len(articles["negative"]) > 0 else "無",
    popularity_article = articles_popularity if len(articles["popularity"]) > 0 else "無",
    address_1          = address[0] if len(address) > 0 else "無",
    address_2          = address[1] if len(address) > 1 else "無",
    address_3          = address[2] if len(address) > 2 else "無",
    positive_count     = sentiment_count["positive_count"],
    negative_count     = sentiment_count["negative_count"],
  ).strip()
  return bard.get_answer(prompt)['content']

def summarize_by_city(topic: str, articles, sentiment_count, city, word_count = 150):

  instruction = """
  你是一個文章摘要生成器，將會閱讀的文章後，提供使用者文章中對主題的摘要。
  摘要內容只需且必須要列出這5點，並用粗體把標題標註。
  1. 事件經過
  2. {city}民眾評價看法
  3. 正負向討論點
  4. 討論熱點
  5. 結論
  正負向討論點，分為正向與負向，先一個大標正負向討論點，再分別列出正向與負向的討論點。
  不要寫補充說明、調整說明、修改說明、字數說明、日期說明等等。
  你將會獲得某個地區中討論的正向、負向與最熱門的文章，以及正負向的討論數量，
  將接收到的內容，經過總結後寫摘要，
  約{word_count}字左右，專注於寫新聞的內容。
  不要寫怎麼調整，不要寫調整說明，不要把新聞的日期寫出來，不要寫什麼需要修改，不要寫修改，不要寫字數，而是專注於寫新聞的內容。
  主題: ###{topic}###
  正向文章: 
  ###
    {positive_article}
  ###
  負向文章: 
  ###
    {negative_article}
  ###
  最熱門文章: 
  ###
    {popularity_article}
  ###
  討論地區: ###{city}###
  正負向討論數量: 
  ###
    正向: {positive_count} 負向: {negative_count}
  ###
  摘要: """

  articles_positive = "---\n".join(articles["positive"])[:800]
  articles_negative = "---\n".join(articles["negative"])[:800]
  articles_popularity = "---\n".join(articles["popularity"])[:800]

  prompt = instruction.format(
    word_count         = word_count,
    topic              = topic, 
    positive_article   = articles_positive  if len(articles["positive"]) > 0 else "無",
    negative_article   = articles_negative   if len(articles["negative"]) > 0 else "無",
    popularity_article = articles_popularity if len(articles["popularity"]) > 0 else "無",
    city               = city,
    positive_count     = sentiment_count["positive_count"],
    negative_count     = sentiment_count["negative_count"],
  ).strip()
  return bard.get_answer(prompt)['content']

def getArticleByKeyAndField(key, field):
  articleDictBydate = cache.hget(key, field).decode()
  articleDictBydate = json.loads(articleDictBydate)
  sorted_dates = sorted(
    articleDictBydate.keys(),
    key=lambda date: datetime.datetime.strptime(date, "%Y-%m-%d"),
  )
  
  merged = []
  for date in sorted_dates:
    merged += [shrink_spaces_and_newlines(article)[:400] for article in articleDictBydate[date]]

  return merged

def getArticlesSentimentByKey(key):
  return {
    "positive_count": cache.hget(key, "PositiveNumber").decode(),
    "negative_count": cache.hget(key, "NegativeNumber").decode(),
  }

def getAddressByKey(key):
  addresses = cache.hget(key, "AddressArticle").decode()
  addresses = json.loads(addresses)
  return [ city_translation.get(x["AddressName"], x["AddressName"]) for x in addresses]

def isArticlesEmpty(articles):
  return len(articles.get("positive", [])) == 0 and len(articles.get("negative", [])) == 0 and len(articles.get("popularity", [])) == 0
