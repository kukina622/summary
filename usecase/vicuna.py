from threading import Thread
from transformers import AutoTokenizer, TextIteratorStreamer
from auto_gptq import AutoGPTQForCausalLM

tokenizer = None
model = None

def load_model():
  global tokenizer, model
  tokenizer = AutoTokenizer.from_pretrained("fireballoon/baichuan-vicuna-chinese-7b-gptq", use_fast=False)
  model = AutoGPTQForCausalLM.from_quantized("fireballoon/baichuan-vicuna-chinese-7b-gptq", device="cuda:0")


def summarize(text: str) -> TextIteratorStreamer:
  if tokenizer is None or model is None:
    load_model()

  instruction = """
  You are a news summarizer, providing chinese concise and objective summaries of current events and important news stories from around the world.
  Offer context and background information to help users understand the significance of the news,
  and keep them informed about the latest developments in a clear and balanced manner.
  Only key points need to be listed, without adding elements that do not exist in the article.
  Please use line breaks when appropriate to make the text easy to read.
  News: {} Summary:
  """
  prompt = instruction.format(text).replace("\n","")
  input_ids = tokenizer(prompt, return_tensors='pt').input_ids.cuda()
  streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
  generation_kwargs = dict(input_ids, streamer=streamer, max_new_tokens=1024)
  thread = Thread(target=model.generate, kwargs=generation_kwargs)
  thread.start()
  return streamer
