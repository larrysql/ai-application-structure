from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    instructions="你是一位AI技术助手，请用简洁中文回答。",
    input="请解释大语言模型API是什么。"
)

print(response.output_text)

if response.usage:
    print("Input tokens:", response.usage.input_tokens)
    print("Output tokens:", response.usage.output_tokens)