# AI 应用的结构 02｜AI 提取的信息，为什么不能直接写入数据库？

上一篇，我们用 Python 调用了大语言模型，从一句话中提取个人经历、目标和顾虑。AI 返回的内容看起来很准确，但如果把这种能力放进真实业务，能否直接把结果写进数据库？

这次我们做一个能用的小工具：**从客户留言提取订单信息，检查数据是否合法，生成一份待确认草稿。** 它适用于订单录入、客户留言整理等场景。完整代码见文末 GitHub 仓库。

## 1. 要解决什么问题？

假设一家服装批发店收到客户消息：

> 我要订20包女装，每包1500比索，明天下午送到仓库。

理想的程序不仅要识别商品、数量和单价，还要算出总金额，并且不能把“明天下午”随意变成某个确定日期。更重要的是，**客户发消息不等于已经确认正式订单**。

我们把流程拆成三步：AI 提取信息 → Python 校验 → 保存待确认草稿。今天不接入数据库，也不自动下单。

## 2. 五分钟搭好实验

需要 Python、OpenAI API Key，以及上一篇已经建立的项目。打开 PowerShell，进入实验目录：

```powershell
cd D:\Projects\ai-application-structure\experiments\02-ai-data-validation
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

在 `.env` 中填写 `OPENAI_API_KEY=你的密钥`。**不要把真实密钥放进 `.env.example`，也不要提交 `.env` 到 GitHub。**

核心程序是 `order_extractor.py`，可以在 GitHub 中直接查看和复制。它做了三件事：用 `client.responses.parse()` 提取信息；用 Pydantic 检查字段类型；用 Python 验证数量、价格、币种、日期并计算金额。运行：

```powershell
python order_extractor.py
```

如果提取符合预期，输出会类似下面这样（**示例，不是实测结果**）：

```json
{
  "product": "女装",
  "quantity": 20,
  "unit_price": 1500.0,
  "currency": "PHP",
  "total_amount": 30000.0,
  "delivery_date": null,
  "status": "pending_confirmation"
}
```

程序同时生成 `order_draft.json`。这个文件只是一份草稿，不会创建真实订单。“明天下午”没有提供基准日期，因此日期暂时留空；需要用户后续确认。

## 3. 为什么不用一句 Prompt 直接生成 JSON？

上一篇实验里，我们要求模型返回 JSON，它却在外面加了 Markdown 代码块标记。人能看懂，`json.loads()` 却可能无法解析整个响应。

这次改用 **Structured Outputs**：通过 Pydantic 定义 `OrderInfo`，再交给 SDK 的 `responses.parse()`，要求模型返回符合字段结构的数据。它解决的是“输出能不能被程序接收”的问题，却不能保证“内容一定提取正确”。

例如，客户说的是20包，模型如果误读成200包，即使 JSON 格式完全合法，业务结果仍然是错的。所以程序要自己计算 `total_amount`，检查数量、价格是否大于零，日期是否有效，并在真实下单前让用户确认。生产系统还需要核对原文与提取值、商品、库存和权限。

## 4. 自己动手试三个输入

打开 `order_extractor.py`，替换 `message` 变量，分别测试：

| 输入 | 希望看到的行为 |
|---|---|
| 我要订20包女装，每包1500比索 | 生成待确认草稿 |
| 我要订20包女装，价格还没确定 | 因缺少单价而拒绝 |
| 我要订0包女装，每包1500比索 | 因数量不合法而拒绝 |

这些是**待验证的预期**，不是我们已经测出的结果。模型可能提取错误，因此要实际运行、记录输出。项目还提供不需要 API 的规则测试：

```powershell
python -m unittest -v test_validation.py
```

这类测试验证的是 Python 校验逻辑，而不是 AI 的理解能力。两者应该分开测试。

## 5. 这个小工具能用在哪里？

订单信息只是一个例子。同样的结构也能用于简历解析、客户需求整理、会议待办提取，甚至 AI 产品中的长期记忆候选信息提取。区别只在于字段和业务规则。

本篇最重要的收获不是学会了某个 API，而是掌握一条工程原则：**让 AI 处理不规则的语言，让程序执行明确的规则；涉及真实业务状态的操作，还要有确认环节。**

本文只是教学实验：尚未实现订单数据库、重复提交防护、商品匹配、真实库存检查或正式订单确认流程，不能直接投入自动下单业务。

---

**完整代码与复现说明**：https://github.com/larrysql/ai-application-structure/tree/main/experiments/02-ai-data-validation

实验文件：`order_extractor.py`、`test_validation.py`、`requirements.txt`、`.env.example`、`README.md`。

下一篇，我们可以把“待确认草稿”真正接入数据库，并处理确认、取消和重复提交。
