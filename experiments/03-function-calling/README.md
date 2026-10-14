# 实验 03：Function Calling 库存查询助手

本实验使用模拟库存，不连接数据库、不创建订单。代码需使用你自己的 OpenAI API Key 运行，调用会产生费用。

## 快速运行

```powershell
cd experiments/03-function-calling
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，将占位符替换为自己的 API Key，切勿提交到 GitHub
python inventory_assistant.py
```

修改文件末尾 `question` 可测试：

- `男装还有多少库存？`
- `童装有50包吗？`
- `你们今天几点关门？`
- `鞋子还有多少库存？`

程序会打印实际工具调用参数、查询结果和模型回答。模型不保证每次都调用工具，也不保证文字完全相同。当前演示只处理一轮工具调用；生产系统需补充多轮调用、超时、错误处理、权限及日志审计。
