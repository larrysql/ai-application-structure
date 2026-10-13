"""Experiment 02: extract a draft order, validate it, never create a real order."""
from pathlib import Path
from datetime import date
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

load_dotenv(Path(__file__).with_name('.env'))
client = OpenAI()

class OrderInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product: str | None
    quantity: int | None
    unit_price: float | None
    currency: str | None
    delivery_date: str | None

class OrderDraft(BaseModel):
    product: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    currency: str
    total_amount: float
    delivery_date: str | None
    status: Literal["pending_confirmation"]

def extract_order(message: str) -> OrderInfo:
    response = client.responses.parse(
        model="gpt-4.1-mini",
        instructions=(
            "从客户消息提取商品、数量、单价、币种和送货日期。"
            "只能提取明确给出的信息，不得猜测。"
            "若日期是‘明天’等相对日期且未提供基准日期，delivery_date返回null。"
            "只有明确的YYYY-MM-DD日期才填写delivery_date；缺失字段返回null。"
            "数量指商品数量，单价指每单位价格。"
        ),
        input=message,
        text_format=OrderInfo,
    )
    if response.output_parsed is None:
        raise ValueError("模型未返回可解析的数据（可能拒答或输出不完整）")
    return response.output_parsed

def validate_order(info: OrderInfo) -> OrderDraft:
    if not info.product or not info.product.strip():
        raise ValueError("缺少商品名称")
    if info.quantity is None or info.quantity <= 0:
        raise ValueError("数量必须大于0")
    if info.unit_price is None or info.unit_price <= 0:
        raise ValueError("单价必须大于0")
    if not info.currency or not info.currency.strip():
        raise ValueError("缺少币种")
    if info.delivery_date is not None:
        try:
            date.fromisoformat(info.delivery_date)
        except ValueError as exc:
            raise ValueError("日期必须为有效的YYYY-MM-DD") from exc
    return OrderDraft(
        product=info.product.strip(),
        quantity=info.quantity,
        unit_price=info.unit_price,
        currency=info.currency.strip(),
        total_amount=round(info.quantity * info.unit_price, 2),
        delivery_date=info.delivery_date,
        status="pending_confirmation",
    )

def main() -> None:
    message = "我要订20包女装，每包1500比索，明天下午送到仓库。"
    info = extract_order(message)
    draft = validate_order(info)
    print("原始消息：", message)
    print("订单草稿：")
    print(draft.model_dump_json(indent=2))
    output = Path(__file__).with_name("order_draft.json")
    output.write_text(draft.model_dump_json(indent=2), encoding="utf-8")
    print("草稿已保存：", output)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"订单处理失败：{exc}")
        raise SystemExit(1)
