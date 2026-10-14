import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 模拟仓库库存
INVENTORY = {"女装": 120, "男装": 80, "童装": 35}


def get_inventory(product: str) -> dict:
    if product not in INVENTORY:
        return {"found": False, "product": product, "quantity": None}
    return {"found": True, "product": product, "quantity": INVENTORY[product]}


tools = [
    {
        "type": "function",
        "name": "get_inventory",
        "description": "查询指定商品的当前库存数量，单位为包",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "商品名称，如女装、男装、童装",
                }
            },
            "required": ["product"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


def ask_inventory(question: str) -> str:
    messages = [{"role": "user", "content": question}]
    instructions = (
        "你是服装批发店的库存助手。涉及库存数量时必须调用工具，"
        "不能猜测库存。只根据工具返回的库存数据回答。"
        "如果不知道营业时间等信息，应明确说明不知道。"
        "可以比较库存是否充足，但不得创建订单或承诺预留库存。"
    )
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=instructions,
        input=messages,
        tools=tools,
    )
    messages.extend(response.output)
    tool_called = False
    for item in response.output:
        if item.type != "function_call":
            continue
        tool_called = True
        if item.name != "get_inventory":
            raise ValueError("不支持的工具")
        args = json.loads(item.arguments)
        product = args["product"]
        if not isinstance(product, str):
            raise ValueError("商品名称必须是字符串")
        result = get_inventory(product)
        print("工具调用：", item.name)
        print("工具参数：", args)
        print("查询结果：", result)
        messages.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(result, ensure_ascii=False),
        })
    if not tool_called:
        return response.output_text
    final_response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=instructions,
        input=messages,
        tools=tools,
        tool_choice="none",
    )
    return final_response.output_text


if __name__ == "__main__":
    question = "女装还有多少库存？我想订50包。"
    answer = ask_inventory(question)
    print("\nAI 回答：")
    print(answer)
