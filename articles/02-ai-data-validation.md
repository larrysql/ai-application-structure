# AI 应用的结构 02｜AI 提取的信息，为什么不能直接写入数据库？

上一篇，我们用 Python 调用了大语言模型，让 AI 从一段自然语言中提取个人经历、目标和顾虑。

程序运行成功，AI 也返回了看起来正确的 JSON 数据。

但如果我们准备把这些数据保存到数据库，一个新的问题就出现了：**AI 返回的内容，真的可以直接使用吗？**

这篇我们做一个小实验：让 AI 从客户留言中提取订单信息，验证数据格式，再决定是否保存。

这个实验可以应用于客户留言整理、订单录入、简历解析、表单自动填写等场景。

## 一、先看一个实际问题

假设我们经营一家服装批发店，客户发来一条消息：

> 我要订 20 包女装，每包 1500 比索，明天下午送到仓库。

我们希望 AI 自动提取出订单数据：

```json
{
  "product": "女装",
  "quantity": 20,
  "unit_price": 1500,
  "total_amount": 30000,
  "delivery_date": null
}
```

这里有个细节：客户说的是“明天下午”，而不是一个明确的日期。如果程序没有提供当前日期，AI 就不应该擅自猜测具体送货日期。

更重要的是，客户只是发送了一条消息，并没有完成订单确认。即使提取结果完全正确，也不应该直接创建正式订单。

因此，我们需要区分三个步骤：

**AI 提取信息 → 程序验证数据 → 业务确认后保存。**

接下来用 Python 实现前两个步骤，并把结果保存为一个本地 JSON 文件，作为待确认的订单草稿。

## 二、准备实验环境

继续使用上一篇的项目目录，新建第二个实验：

```text
experiments/
└── 02-ai-data-validation/
    ├── order_extractor.py
    ├── requirements.txt
    └── .env.example
```

安装依赖：

```bash
pip install --upgrade openai python-dotenv pydantic
```

API Key 仍然保存在本地 `.env` 文件中，不要上传 GitHub。

`requirements.txt`：

```text
openai>=2.0.0,<4.0.0
python-dotenv>=1.0.0,<2.0.0
pydantic>=2.0.0,<3.0.0
```

## 三、编写一个真正能使用的信息提取程序

创建 `order_extractor.py`：

```python
import json
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()
client = OpenAI()


# 1. 定义程序需要的数据结构
class OrderInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str | None
    quantity: int | None
    unit_price: float | None
    delivery_date: str | None


# 2. 定义经过程序验证的订单草稿
class OrderDraft(BaseModel):
    product: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    total_amount: float
    delivery_date: str | None
    status: Literal["pending_confirmation"]


# 3. 让 AI 提取客户信息
def extract_order(message: str) -> OrderInfo:
    response = client.responses.parse(
        model="gpt-4.1-mini",
        instructions=(
            "从客户消息中提取商品、数量、单价和送货日期。"
            "只提取明确提供的信息，不要猜测。"
            "日期必须是明确的YYYY-MM-DD格式。"
            "如果只有'明天'等相对日期且没有"
            "提供基准日期，返回null。"
            "缺失字段返回null。"
        ),
        input=message,
        text_format=OrderInfo,
    )

    if response.output_parsed is None:
        raise ValueError("模型未返回可解析的订单信息")

    return response.output_parsed


# 4. 程序独立校验业务数据
def validate_order(info: OrderInfo) -> OrderDraft:
    if not info.product:
        raise ValueError("缺少商品名称")

    if info.quantity is None or info.quantity <= 0:
        raise ValueError("数量必须大于0")

    if info.unit_price is None or info.unit_price <= 0:
        raise ValueError("单价必须大于0")

    return OrderDraft(
        product=info.product,
        quantity=info.quantity,
        unit_price=info.unit_price,
        total_amount=round(
            info.quantity * info.unit_price, 2
        ),
        delivery_date=info.delivery_date,
        status="pending_confirmation",
    )


# 5. 运行实验
message = (
    "我要订20包女装，每包1500比索，"
    "明天下午送到仓库。"
)

try:
    info = extract_order(message)
    draft = validate_order(info)

    print("订单草稿：")
    print(draft.model_dump_json(indent=2))

    # 只保存待确认草稿，不创建正式订单
    output = Path("order_draft.json")
    output.write_text(
        draft.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print(f"\n草稿已保存到：{output}")

except Exception as e:
    print(f"订单处理失败：{e}")
```

这段程序虽然比上一篇稍长，但核心只有三件事：让模型提取数据、由程序验证数据、保存待确认草稿。

其中最值得关注的是 `client.responses.parse()`。

上一篇，我们只是通过 Prompt 要求 AI 返回 JSON，结果模型在 JSON 外面加上了 Markdown 代码块标记，导致整个响应无法直接解析。

这次我们使用 Structured Outputs，让模型按照 `OrderInfo` 定义的结构生成数据，并通过 SDK 解析为 Python 对象。

不过，结构化输出解决的是格式约束问题，并不保证模型提取的每个数值都正确。所以程序仍然需要独立检查。

例如，数量必须大于零，单价必须大于零，而总金额由 Python 自己计算，不交给 AI 猜测。

## 四、运行程序，观察结果

在 PowerShell 中执行：

```powershell
cd D:\Projects\ai-application-structure\experiments\02-ai-data-validation

python order_extractor.py
```

如果模型正确提取信息，程序预期生成类似下面的草稿：

```json
{
  "product": "女装",
  "quantity": 20,
  "unit_price": 1500.0,
  "total_amount": 30000.0,
  "delivery_date": null,
  "status": "pending_confirmation"
}
```

注意：这是**预期输出示例，不是已经完成的实测结果**。实际结果需要运行程序后确认。

如果客户没有提供价格，程序就应该拒绝生成完整订单草稿，而不是擅自补一个价格。

如果客户说“订 0 包女装”，程序也应该因为数量不符合规则而拒绝处理。

这些验证并不需要 AI 完成，普通 Python 程序反而更加可靠。

## 五、为什么有了 Structured Outputs，还需要程序校验？

这里涉及 AI 应用开发中一个非常重要的区别。

Structured Outputs 主要保证模型按照规定的数据结构生成输出。例如，我们要求 `quantity` 是整数、`unit_price` 是数字，模型就需要按照对应的 Schema 组织数据。

但它无法替我们判断所有业务规则。

例如，客户说“20 包，每包 1500”，模型却错误提取成了 200 包。即使返回的是完全合法的 JSON，业务数据仍然是错误的。

再比如，客户说“先问问价格”，模型却把它当成正式下单。如果程序直接写入数据库，就可能产生一笔根本不存在的订单。

因此，我们至少需要建立三道防线：

| 层次 | 解决什么问题 |
|---|---|
| 结构化输出 | 数据格式和字段类型是否符合要求 |
| 程序校验 | 数量、价格、金额等是否满足业务规则 |
| 人工或业务确认 | 用户是否真的想执行这项操作 |

在真实系统中，还需要进一步检查商品是否存在、库存是否充足、客户是否有权限下单，以及是否重复提交。

这也是为什么 AI 可以帮助我们理解自然语言，却不应该绕过原有的业务规则。

## 六、再做三个测试

把代码中的 `message` 分别替换为以下内容，观察程序如何处理：

| 测试 | 客户消息 | 期望行为 |
|---|---|---|
| A | 我要订20包女装，每包1500比索 | 生成待确认草稿 |
| B | 我要订20包女装，价格还没确定 | 拒绝生成完整草稿 |
| C | 我要订0包女装，每包1500比索 | 拒绝生成完整草稿 |

这三个测试可以帮助我们验证程序是否只接受符合规则的数据。

当然，三个测试还远远不够。真实产品需要更多测试样本，尤其是模糊表达、信息冲突和异常输入。

## 七、从一个小实验，到真实 AI 产品

这个实验看起来只是提取一条订单消息，但背后的设计思路可以应用到很多场景。

例如，AI 可以从用户的一段生活描述中识别个人经历、目标和约束，但这些信息不能未经确认就进入用户的长期记忆。

同样，AI 可以阅读一封邮件并提取付款信息，却不应该仅凭邮件内容就自动执行付款。

**AI 负责理解不规则的自然语言，程序负责执行确定的业务规则。**

两者结合，才有可能构建真正可靠的应用。

本篇我们还没有连接数据库，只是把通过验证的数据保存为本地 JSON 草稿。下一步可以加入数据库，研究如何设计待确认、已确认和已取消等状态，并确保重复请求不会创建重复订单。

---

### 本文实验代码

GitHub：https://github.com/larrysql/ai-application-structure

实验目录：`experiments/02-ai-data-validation/`

本文使用 Python、OpenAI API 和 Pydantic 实现自然语言订单信息提取、结构化输出及业务数据校验。代码可以自行运行和修改，API 调用可能产生少量费用。