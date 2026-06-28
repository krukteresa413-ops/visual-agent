"""Credits routes — 真实积分余额与充值订单(图四).

- GET /api/v1/credits/balance  鉴权:当前用户积分余额
- GET /api/v1/credits/orders   鉴权:当前用户充值订单列表
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import User
from app.models.credit import CreditOrder
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/v1/credits", tags=["credits"])


@router.get("/balance")
def balance(current_user: User = Depends(get_current_user)):
    return {"credits": current_user.credits or 0}


@router.get("/orders")
def orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(CreditOrder)
        .filter(CreditOrder.user_id == current_user.id)
        .order_by(CreditOrder.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "orders": [
            {
                "out_trade_no": r.out_trade_no,
                "amount_fen": r.amount_fen,
                "credits": r.credits,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "paid_at": r.paid_at.isoformat() if r.paid_at else None,
            }
            for r in rows
        ]
    }
