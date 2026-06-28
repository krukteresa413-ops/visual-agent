"""Alipay payment routes — 图四 沙箱脚手架.

- GET  /api/v1/payment/tiers          公开:充值档位
- POST /api/v1/payment/alipay/create  鉴权:建单 + 返回收银台跳转 URL
- POST /api/v1/payment/alipay/notify  支付宝异步回调:验签 -> 幂等加积分
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import User
from app.models.credit import CreditOrder
from app.services.auth_service import get_current_user
from app.services import payment_service

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])


class CreateOrderRequest(BaseModel):
    amount_fen: int


@router.get("/tiers")
def tiers():
    return {"tiers": payment_service.RECHARGE_TIERS}


@router.post("/alipay/create")
def create_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tier = payment_service.get_tier(req.amount_fen)
    if tier is None:
        raise HTTPException(status_code=400, detail="invalid amount")

    config = payment_service.load_config()
    if config is None:
        raise HTTPException(status_code=503, detail="alipay not configured")

    order = CreditOrder(
        out_trade_no=payment_service.generate_out_trade_no(),
        user_id=current_user.id,
        amount_fen=tier["amount_fen"],
        credits=tier["credits"],
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    pay_url = payment_service.build_page_pay_url(
        config,
        out_trade_no=order.out_trade_no,
        amount_fen=order.amount_fen,
        subject=f"MOYAG 积分充值 {tier['credits']}",
    )
    return {"out_trade_no": order.out_trade_no, "pay_url": pay_url, "credits": order.credits}


@router.post("/alipay/notify")
async def alipay_notify(request: Request, db: Session = Depends(get_db)):
    """支付宝异步通知:必须验签;成功返回纯文本 success(否则支付宝重发)。"""
    config = payment_service.load_config()
    if config is None:
        return PlainTextResponse("failure")

    form = await request.form()
    params = {k: v for k, v in form.items()}

    if not payment_service.verify(params, config.alipay_public_key):
        return PlainTextResponse("failure")

    if params.get("trade_status") not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        # 其它状态(如 WAIT_BUYER_PAY)直接 ack,不加分
        return PlainTextResponse("success")

    payment_service.grant_credits(
        db,
        out_trade_no=params.get("out_trade_no", ""),
        alipay_trade_no=params.get("trade_no"),
    )
    return PlainTextResponse("success")
