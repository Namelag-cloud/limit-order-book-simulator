import random
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


def make_market_order(
    order_id,
    trader_id,
    side,
    quantity,
    asset="BTC"
):
    return Order(
        order_id=order_id,
        trader_id=trader_id,
        timestamp=datetime.now(),

        side=side,
        order_type=OrderType.MARKET,

        price=None,
        asset=asset,

        quantity=quantity,
        remaining_quantity=quantity,

        status=OrderStatus.ACTIVE
    )


def generate_random_limit_order(
    order_id,
    trader_id,
    reference_price,
    asset="BTC",
    max_price_offset=20,
    max_quantity=10
):
    side = random.choice([
        Side.BUY,
        Side.SELL
    ])

    price_offset = random.randint(
        -max_price_offset,
        max_price_offset
    )

    price = reference_price + price_offset

    quantity = random.randint(
        1,
        max_quantity
    )

    return make_limit_order(
        order_id=order_id,
        trader_id=trader_id,
        side=side,
        price=price,
        quantity=quantity,
        asset=asset
    )


def generate_random_order(
    order_id,
    trader_id,
    reference_price,
    asset="BTC",
    market_order_probability=0.20,
    max_price_offset=20,
    max_quantity=10
):
    side = random.choice([
        Side.BUY,
        Side.SELL
    ])

    quantity = random.randint(
        1,
        max_quantity
    )

    if random.random() < market_order_probability:

        return make_market_order(
            order_id=order_id,
            trader_id=trader_id,
            side=side,
            quantity=quantity,
            asset=asset
        )

    price_offset = random.randint(
        -max_price_offset,
        max_price_offset
    )

    price = reference_price + price_offset

    return make_limit_order(
        order_id=order_id,
        trader_id=trader_id,
        side=side,
        price=price,
        quantity=quantity,
        asset=asset
    )

class RandomOrderGenerator:

    def __init__(
        self,
        reference_price,
        asset="BTC",
        market_order_probability=0.20,
        max_price_offset=20,
        max_quantity=10
    ):
        self.reference_price = reference_price
        self.asset = asset

        self.market_order_probability = (
            market_order_probability
        )

        self.max_price_offset = max_price_offset
        self.max_quantity = max_quantity

    def generate(
        self,
        order_id,
        trader_id
    ):
        return generate_random_order(
            order_id=order_id,
            trader_id=trader_id,
            reference_price=self.reference_price,
            asset=self.asset,
            market_order_probability=self.market_order_probability,
            max_price_offset=self.max_price_offset,
            max_quantity=self.max_quantity
        )


