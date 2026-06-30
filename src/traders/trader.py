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
class Portfolio:

    cash: float
    reserved_cash: float = 0.0


    inventory: dict[str, int] = field(default_factory=dict)
    reserved_inventory :dict[str, int] = field(default_factory=dict)

    volume_traded: dict[str, int] = field(default_factory=dict)

    realized_pnl: float = 0.0

    def market_value(self, prices: dict[str, float]) -> float:

        value = self.cash

        for asset, quantity in self.inventory.items():
            value += quantity * prices[asset]

        return value

    def buy(self, asset: str, quantity: int, price: int):

        cost = quantity * price

        self.cash -= cost

        self.inventory[asset] = (
            self.inventory.get(asset, 0) + quantity
        )

        self.volume_traded[asset] = (
            self.volume_traded.get(asset, 0) + quantity
        )

    def sell(self, asset: str, quantity: int, price: int):

        current = self.inventory.get(asset, 0)

        self.cash += quantity * price

        self.inventory[asset] = current - quantity

        self.volume_traded[asset] = (
            self.volume_traded.get(asset, 0) + quantity
        )   

    
    def reserve_cash(
        self,
        amount: float,
    ):
        self.reserved_cash += amount

    
    def release_cash(
        self,
        amount: float,
    ):
        self.reserved_cash -= amount

    def reserve_inventory(
        self,
        asset: str,
        quantity: int,
    ):
        self.reserved_inventory[asset] = (
            self.reserved_inventory.get(asset, 0)
            + quantity
        )


    def release_inventory(
        self,
        asset: str,
        quantity: int,
    ):
        self.reserved_inventory[asset] = (
            self.reserved_inventory.get(asset, 0)
            - quantity
        )   


@dataclass
class Trader:

    trader_id: int

    portfolio: Portfolio

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

    max_order_age: int = 100



    def step(self, exchange):


        if self.active_orders:

            oldest_order = min(
                self.active_orders.values(),
                key=lambda order: order.created_tick,
            )

            age = exchange.current_tick - oldest_order.created_tick

            if age >= self.max_order_age:
                return oldest_order.order_id
                

        asset = random.choice([
            "BTC",
            "ETH"
        ])

        reference_price = exchange.last_trade_price[asset] # update this to an actual economic model 
       
        owned = self.portfolio.inventory.get(asset, 0)

        reserved = self.portfolio.reserved_inventory.get(
            asset,
            0
        )

        available = owned - reserved # actual owning

        if available == 0:
            side = Side.BUY

        else:
            side = random.choice([
                Side.BUY,
                Side.SELL
            ])

        is_market = random.random() < self.market_order_probability
        
        if is_market:
            trade_price = reference_price

        else:

            offset = random.randint(
                -self.max_price_offset,
                self.max_price_offset
            )

            trade_price = max(
                100,
                reference_price
                + offset
            )

        if trade_price <= 0:
            return None

        if side == Side.BUY:

            available_cash = (
                self.portfolio.cash
                - self.portfolio.reserved_cash
            )

            max_affordable = int(
                available_cash // trade_price
            )

            max_quantity = min(
                self.max_quantity,
                max_affordable
            )

        else:
            max_quantity = min(
                self.max_quantity,
                available
            )


        
        if max_quantity <= 0:
            return None

        quantity = random.randint(
            1,
            max_quantity
        )

        if is_market:
            return make_market_order(trader_id=self.trader_id, side=side,quantity=quantity,asset=asset)

        else:
            return make_limit_order(trader_id=self.trader_id,side=side,price=trade_price,quantity=quantity,asset=asset)
