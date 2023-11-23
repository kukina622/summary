import configparser
from bardapi import Bard
import redis
import re
import datetime
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
  你將會獲得正向、負向與最熱門的文章，
  還有最多討論的地區前三名，以及正負向的討論數量，與終端用戶的角色，
  將接收到的內容，經過總結後寫出角色想看的摘要，
  內容需要
  1. 事件經過
  2. 大眾評價看法
  3. 正負向討論點
  約{word_count}字左右，不要寫日期，專注於寫新聞的內容，給終端用戶看的。
  地區、正負向討論數量都要列出來。
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

  articles["positive"] = shrink_spaces_and_newlines(articles["positive"])
  articles["negative"] = shrink_spaces_and_newlines(articles["negative"])
  articles["popularity"] = shrink_spaces_and_newlines(articles["popularity"])

  prompt = instruction.format(
    word_count         = word_count,
    topic              = topic, 
    positive_article   = articles["positive"][:600]   if articles["positive"] != "" else "無",
    negative_article   = articles["negative"][:600]   if articles["negative"] != "" else "無",
    popularity_article = articles["popularity"][:600] if articles["popularity"] != "" else "無",
    address_1          = address[0] if len(address) > 0 else "無",
    address_2          = address[1] if len(address) > 1 else "無",
    address_3          = address[2] if len(address) > 2 else "無",
    positive_count     = sentiment_count["positive_count"],
    negative_count     = sentiment_count["negative_count"],
  ).strip()
  print(prompt)
  return bard.get_answer(prompt)['content']

def summarize_by_city(topic: str, articles, sentiment_count, city, word_count = 150):

  instruction = """
  你是一個文章摘要生成器，將會閱讀的文章後，提供使用者文章中對主題的摘要。
  你將會獲得某個地區討論事件中的正向、負向與最熱門的文章，以及正負向的討論數量，
  與終端用戶的角色，將接收到的內容，經過總結後寫出角色會想看的摘要，
  約{word_count}字左右，不要寫日期，專注於寫新聞的內容，給終端用戶看的。
  專注於寫新聞的內容，不要寫怎麼調整，不要寫調整說明，不要把新聞的日期寫出來，不要寫什麼需要修改，不要寫修改，終端用戶不在乎。
  地區、正負向討論數量都要列出來。
  講到正向/負向/最熱門文章的時候，用粗體稍微標註一下。
  講摘要的時候，講具體一點，也稍微介紹一下該事件，不要講太多。
  主題: 
  {topic}
  正向文章: 
  {positive_article}
  負向文章: 
  {negative_article}
  最熱門文章: 
  {popularity_article}
  討論地區: {city}
  正負向討論數量:
  正向: {positive_count} 負向: {negative_count}
  摘要: """

  articles["positive"] = shrink_spaces_and_newlines(articles["positive"])
  articles["negative"] = shrink_spaces_and_newlines(articles["negative"])
  articles["popularity"] = shrink_spaces_and_newlines(articles["popularity"])

  prompt = instruction.format(
    word_count         = word_count,
    topic              = topic, 
    positive_article   = articles["positive"][:600]   if articles["positive"] != "" else "無",
    negative_article   = articles["negative"][:600]   if articles["negative"] != "" else "無",
    popularity_article = articles["popularity"][:600] if articles["popularity"] != "" else "無",
    city               = city,
    positive_count     = sentiment_count["positive_count"],
    negative_count     = sentiment_count["negative_count"],
  ).strip()

  return bard.get_answer(prompt)['content']

def getArticleByKeyAndField(key, field):
  aticleDictBydate = cache.hget(key, field).decode()
  aticleDictBydate = json.loads(aticleDictBydate)
  sorted_dates = sorted(
      aticleDictBydate.keys(),
      key=lambda date: datetime.datetime.strptime(date, "%Y-%m-%d"),
      reverse=True)

  for date in sorted_dates:
    if len(aticleDictBydate[date]) > 0:
      return aticleDictBydate[date][0]
  return ""

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
  return articles.get("positive", "") == "" and articles.get("negative", "") == "" and articles.get("popularity", "") == ""
