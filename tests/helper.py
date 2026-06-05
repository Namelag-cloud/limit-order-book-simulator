

from datetime import datetime

from src.core import (
    Order,
    Side,
    OrderType,
    OrderStatus
)

def make_limit_order(
    order_id,
    trader_id,
    side,
    price,
    quantity,
    asset="BTC"
):
    return Order(
        order_id=order_id,
        trader_id=trader_id,
        timestamp=datetime.now(),

        side=side,
        order_type=OrderType.LIMIT,

        price=price,
        asset=asset,

        quantity=quantity,
        remaining_quantity=quantity,

        status=OrderStatus.ACTIVE
    )