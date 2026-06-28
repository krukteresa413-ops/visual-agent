"""Credit order model — backs Alipay recharge (图四 支付宝沙箱脚手架).

One row per Alipay order. `out_trade_no` is unique so the async notify
callback can grant credits idempotently (Alipay re-sends notifications).
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class CreditOrder(Base):
    __tablename__ = "credit_orders"

    id = Column(Integer, primary_key=True, index=True)
    out_trade_no = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount_fen = Column(Integer, nullable=False)          # 支付金额(分)
    credits = Column(Integer, nullable=False)             # 到账积分
    status = Column(String(20), nullable=False, default="pending")  # pending | paid
    alipay_trade_no = Column(String(64), nullable=True)   # 支付宝交易号(回调写入)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
