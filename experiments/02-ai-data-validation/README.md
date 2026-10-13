# Experiment 02：AI 订单信息提取与校验

对应文章：`../../articles/02-ai-data-validation.md`

## 快速开始（PowerShell）

```powershell
cd D:\Projects\ai-application-structure\experiments\02-ai-data-validation
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 用编辑器打开 .env，填写自己的真实 API Key；绝不要提交到 GitHub
python order_extractor.py
```

运行后在本目录生成 `order_draft.json`（已被 `.gitignore` 排除）。输出只代表待确认草稿，**不会创建正式订单**。

## 不调用 API 的业务规则测试

```powershell
python -m unittest -v test_validation.py
```

## AI 提取测试建议

在 `order_extractor.py` 中分别替换 `message`，观察真实输出：

1. `我要订20包女装，每包1500比索`：期望形成待确认草稿。
2. `我要订20包女装，价格还没确定`：期望因缺少单价而拒绝。
3. `我要订0包女装，每包1500比索`：期望因数量不合法而拒绝。

**注意**：这是待运行的实验，不提供伪造的实测结果。结构化输出只保证形状，不保证模型提取的数值忠实于原文。实际生产环境还需要人工确认、商品匹配、权限校验、币种精度、幂等控制与数据库事务。
