# AI 应用的结构 03｜让 AI 查询库存：Function Calling 究竟怎么用？

假设你经营一家服装批发店，客户发来一条消息：“女装还有多少库存？我想订 50 包。”

如果把这句话直接发给大语言模型，它并不知道仓库里还有多少货。模型可能会告诉你应该如何查询库存，但无法凭空知道真实数量。

我们希望实现的是另一种效果：**AI 理解客户的问题，自动调用库存查询程序，再根据查询结果回答客户。**

这就是 Function Calling，也叫工具调用。

这一篇，我们用 Python 实现一个简单的库存查询助手。不需要搭建数据库，也不需要复杂的 Agent 框架，只需要一个普通的 Python 函数和一次完整的工具调用流程。

## 一、先看我们要实现什么

假设仓库里有以下库存：

| 商品 | 当前库存 |
|---|---:|
| 女装 | 120 包 |
| 男装 | 80 包 |
| 童装 | 35 包 |

客户问：“女装还有多少库存？我想订 50 包。”

程序需要完成三件事：理解客户要查询女装库存，调用 Python 函数获得真实库存，再判断现有库存是否足够满足客户提出的数量。

```text
客户提出问题
      ↓
AI 判断需要查询库存
      ↓
AI 请求调用 get_inventory()
      ↓
Python 执行库存查询
      ↓
查询结果返回给 AI
      ↓
AI 根据真实数据回答客户
```

这里有一个容易误解的地方：**不是 AI 直接进入数据库查询，而是 AI 告诉我们的程序应该调用哪个工具、传入什么参数。** 真正执行查询的仍然是我们自己的 Python 代码。

这意味着，我们可以继续使用原有的数据库、权限控制和业务规则，而不必把这些能力交给模型。

## 二、准备实验环境

在 GitHub 项目中创建第三个实验目录：

```text
experiments/
└── 03-function-calling/
    ├── inventory_assistant.py
    ├── requirements.txt
    └── .env.example
```

继续使用 OpenAI Python SDK：

```bash
pip install --upgrade openai python-dotenv
```

`requirements.txt`：

```text
openai>=2.0.0,<4.0.0
python-dotenv>=1.0.0,<2.0.0
```

在本地 `.env` 文件中配置 API Key：

```text
OPENAI_API_KEY=你的API_KEY
```

注意，`.env` 只能保存在本地，不要提交到 GitHub。公开的 `.env.example` 应使用占位符。

## 三、编写库存查询程序

新建 `inventory_assistant.py`：

```python
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
```

这段代码看起来比前两篇复杂一点，但真正需要理解的只有三个地方。

首先，`get_inventory()` 是我们自己编写的普通 Python 函数。即使完全不使用 AI，它也能够查询库存。

其次，`tools` 是提供给模型的工具说明书，告诉模型这个函数叫什么、有什么用途、需要哪些参数。

最后，程序收到模型发出的 `function_call` 后，自己执行对应函数，再把查询结果传回模型。

**模型负责决定调用什么，程序负责真正执行。**

需要特别注意：这里的工具名称是由程序明确允许的。不能让模型随意指定 Python 函数名并直接执行，否则可能带来严重的安全风险。

## 四、运行程序，观察工具调用

在 PowerShell 中执行：

```powershell
cd D:\Projects\ai-application-structure\experiments\03-function-calling
python inventory_assistant.py
```

如果模型正确识别了查询意图，控制台预期会出现类似输出：

```text
工具调用： get_inventory
工具参数： {'product': '女装'}
查询结果： {'found': True, 'product': '女装', 'quantity': 120}

AI 回答：
女装目前有120包库存。您计划订购50包，当前库存数量足够。
```

以上只是**预期输出示例，并非实测结果**。具体措辞和工具调用行为以实际运行结果为准。

现在我们已经让 AI 完成了一件以前单纯聊天无法完成的事：获取程序中的业务数据，并利用这些数据回答问题。

当然，本实验使用的是写在 Python 字典中的模拟库存，而不是数据库。如果要查询真正的仓库库存，需要将 `get_inventory()` 替换成数据库查询函数。

## 五、为什么不直接把库存数据发给 AI？

你可能会想，既然只有三个商品，为什么不直接把库存表写进 Prompt，让模型回答？当然可以。但如果商品有几千种，而且库存每天都在变化，问题就不同了。

每次请求都把整个库存表发给模型，不仅浪费 Token，还可能使用过期数据。工具调用提供了更合理的方式：**模型只负责理解查询意图，需要什么数据，就由程序查询什么数据。**

例如，AI 可以调用订单查询函数回答“我的订单发货了吗”，调用物流查询函数回答“货物现在在哪里”，也可以调用计算函数完成需要精确计算的任务。

它们背后的结构其实相同：自然语言输入、模型选择工具、程序执行操作、模型组织回答。这也是很多 AI Agent 应用的基础能力之一。

不过，Function Calling 本身并不等于一个完整的 Agent。一个能够自主规划、多次调用工具并处理失败情况的系统，还需要更多工程设计。

## 六、再做三个测试

现在修改程序最后的 `question`，分别测试：

| 客户问题 | 我们希望观察什么 |
|---|---|
| 男装还有多少库存？ | 是否正确查询男装 |
| 童装有50包吗？ | 是否发现库存不足 |
| 你们今天几点关门？ | 是否避免编造营业时间 |

第三个问题尤其值得测试。我们的工具只有库存查询能力，没有营业时间数据。如果 AI 在不知道营业时间的情况下编造一个答案，就说明仅有工具调用还不足以保证回答可靠。

还可以尝试查询不存在的商品，例如“鞋子还有多少库存”。此时函数会返回 `found: False`，模型应该明确告知无法查到该商品，而不是把库存数量说成零。

## 七、工具调用真正改变了什么？

前两篇，我们让 AI 从文本中提取信息，并通过程序校验结果。第三篇，我们开始让 AI 主动使用程序提供的能力。

这意味着 AI 应用不再局限于生成文字，而是可以与已有的软件系统发生联系。

但这里也存在一个重要边界。查询库存是一种只读操作，即使模型理解错了，通常也只是回答不准确。如果把工具换成“创建订单”“修改价格”或者“执行退款”，风险就会明显增加。

因此，在实际产品中，查询类工具可以相对开放，而涉及修改数据、资金或权限的工具，必须经过更严格的参数校验、权限检查和必要的人工确认。

**AI 可以提出操作请求，但是否允许执行，最终应该由我们的程序决定。**

本篇只实现了一个只读库存查询工具，没有连接数据库，也没有修改任何业务数据。下一步，我们可以继续研究：当一个问题需要查询多个系统、调用多个工具时，应该如何组织整个执行过程？这将逐渐进入 AI Agent 的实际开发。

---

### 本文实验代码

GitHub：https://github.com/larrysql/ai-application-structure

实验目录：`experiments/03-function-calling/`

本篇使用 Python 和 OpenAI API 实现 Function Calling，通过模拟库存数据展示模型如何调用业务函数。API 调用可能产生少量费用。正式发布前应运行实验，核对工具调用记录及实际输出。
