from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    instructions="""
    从用户描述中提取：
    1. 个人经历
    2. 未来目标
    3. 现实顾虑

    请使用JSON格式返回。
    """,
    input="""
    我做了十几年软件开发，
    现在想开发自己的AI产品，
    但担心失去稳定收入。
    """
)

print(response.output_text)