from dataclasses import dataclass, field
from enum import Enum, auto
import random
from src.helper import (
    make_limit_order,
    make_market_order,
    Order,
    Side
)


class Personality(Enum):
    NEUTRAL = auto()


@dataclass
class Trader:

    trader_id: int

    cash: float

    inventory: dict[str, int]

    active_orders: dict[int, Order] = field(
        default_factory=dict
    )

    personality: Personality = Personality.NEUTRAL

    history_enabled: bool = False

    def step(self, exchange):
        raise NotImplementedError


@dataclass
class RandomTrader(Trader):

    market_order_probability: float = 0.20

    max_price_offset: int = 20

    max_quantity: int = 10

    asset: str = "BTC"

    def step(self, exchange):

        side = random.choice([
            Side.BUY,
            Side.SELL
        ])

        quantity = random.randint(
            1,
            self.max_quantity
        )

        reference_price = (
            exchange.last_trade_price
        )

        if (
            random.random()
            < self.market_order_probability
        ):

            order = make_market_order(
                trader_id=self.trader_id,
                side=side,
                quantity=quantity,
                asset=self.asset
            )

        else:

            offset = random.randint(
                -self.max_price_offset,
                self.max_price_offset
            )

            price = (
                reference_price
                + offset
            )

            order = make_limit_order(
                trader_id=self.trader_id,
                side=side,
                price=price,
                quantity=quantity,
                asset=self.asset
            )
    
        return order
