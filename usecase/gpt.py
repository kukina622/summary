import openai
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

openai.api_key = config["gpt"]["API_KEY"]

def summarize(text: str) -> str:
  instruction = """
  You are a news summarizer, providing chinese concise and objective summaries of current events and important news stories from around the world.
  Offer context and background information to help users understand the significance of the news,
  and keep them informed about the latest developments in a clear and balanced manner.
  Only key points need to be listed, without adding elements that do not exist in the article.
  Please use line breaks when appropriate to make the text easy to read.
  News: {} Summary:
  """
  prompt = instruction.format(text).replace("\n","")

  model_engine = "gpt-3.5-turbo-16k"
  completion = openai.Completion.create(engine = model_engine, prompt = prompt, max_tokens = 1024, temperature = 0.8)

  return completion["choices"][0]["text"]
