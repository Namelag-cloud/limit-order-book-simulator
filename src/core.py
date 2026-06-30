from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional
from sortedcontainers import SortedDict
from copy import deepcopy

# ===============================
# Global Variables
# ===============================

TICK_SIZE = 0.01
def ticks_to_price(ticks: int):
    return ticks * TICK_SIZE


# ===============================
# Enum
# ===============================

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(Enum):
    ACTIVE = "ACTIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    FILLED  = "FILLED"


# =========================
# CORE OBJECTS
# =========================
@dataclass
class Order:

    trader_id: int

    timestamp: datetime

    side: Side
    order_type: OrderType

    price: int| None
    asset: str

    quantity: int 
    remaining_quantity: int 

    status: OrderStatus
    
    order_id: int | None = None

    created_tick: int = 0

@dataclass
class Trade:
    trade_id: int

    buy_order_id: int
    sell_order_id: int

    buyer_trader_id: int
    seller_trader_id: int

    asset: str
    price: int
    quantity: int

    resting_side: Side

    timestamp: datetime

# =========================
# ORDER BOOK
# =========================


class OrderBook:

    def __init__(self):
        
        self.bids: dict[str, SortedDict[int, list[Order]]] = {}
        self.asks: dict[str, SortedDict[int, list[Order]]] = {}

        self.order_lookup: dict[int, Order] = {}

        ASSETS = ("BTC", "ETH")
        
        self.bids = {
            asset: SortedDict()
            for asset in ASSETS
        }

        self.asks = {
            asset: SortedDict()
            for asset in ASSETS
        }   

    def add_order(self, order: Order) -> None:

        match order.side:

            case Side.BUY:
                book = self.bids[order.asset]

            case Side.SELL:
                book = self.asks[order.asset]

            case _:
                raise ValueError("Order side can only be BUY or SELL")

        if order.price not in book:
            book[order.price] = []
        
        book[order.price].append(order)            

        self.order_lookup[order.order_id] = order

    def remove_order(self, orderid: int) -> bool:

        if orderid not in self.order_lookup:
            return False

        order = self.order_lookup[orderid]
        

        match order.side:

            case Side.SELL:

                book = self.asks[order.asset]
                book[order.price].remove(order)

                if not book[order.price]:
                    del book[order.price]

            case Side.BUY:

                book = self.bids[order.asset]
                book[order.price].remove(order)

                if not book[order.price]:
                    del book[order.price]

            case _:
                raise ValueError("Order side can only be BUY or SELL, check asset sorting too")

        del self.order_lookup[orderid]

        return True

    def get_best_bid(self, asset: str) -> int | None:

        book = self.bids[asset]

        if not book:
            return None

        return book.peekitem(-1)[0]

    def get_best_ask(self, asset: str) -> int | None:

        book = self.asks[asset]

        if not book:
            return None

        return book.peekitem(0)[0]

    def get_best_bid_order(self, asset: str) -> Order | None:

        best = self.get_best_bid(asset)

        if best is None:
            return None

        return self.bids[asset][best][0]


    def get_best_ask_order(self, asset:str) -> Order | None:

        best = self.get_best_ask(asset)

        if best is None:
            return None

        return self.asks[asset][best][0]

    def display_book(self):
        pass
        



# =========================
# EXCHANGE
# =========================

@dataclass
class ExchangeResult:

    changed_orders: list[Order]

    trades: list[Trade]


class Exchange:
    
    def __init__(self, reference_price: int):
        self.reference_price = reference_price
        self.last_trade_price = {
            "BTC": reference_price,
            "ETH": reference_price,
        }

        self.order_book = OrderBook()

        self.trade_history: list[Trade] = []
        self.submitted_orders: dict[int, Order] = {}

        self.next_order_id = 1
        self.next_trade_id = 1
        self.current_tick: int = 0


    def submit_order(self, order: Order) -> ExchangeResult:

        order.order_id = self.next_order_id
        self.next_order_id += 1

        if not validate_order(order):
            raise ValueError("invalid order")

        self.record_orders(order)

        self.current_tick += 1
        order.created_tick = self.current_tick

        return self.process_order(order)

    def cancel_order(self,order_id: int,) -> ExchangeResult:

        if order_id not in self.order_book.order_lookup:
            raise ValueError("Unknown order ID, trader access/info problem if on a sim run")

        order = self.order_book.order_lookup[order_id]

        order.status = OrderStatus.CANCELLED

        self.order_book.remove_order(order_id)

        return ExchangeResult(
            changed_orders=[order],
            trades=[],
        )


    def process_order(self,incoming_order: Order) -> ExchangeResult:

        changed_orders = {}
        new_trades = []

        while incoming_order.remaining_quantity > 0:  

            if incoming_order.side == Side.BUY:

                resting_order = (
                    self.order_book.get_best_ask_order(incoming_order.asset)
                )

                if resting_order is None:
                    break

                buy_order = incoming_order
                sell_order = resting_order

            else:

                resting_order = (
                    self.order_book.get_best_bid_order(incoming_order.asset)
                )

                if resting_order is None:
                    break

                buy_order = resting_order
                sell_order = incoming_order

            resting_side = resting_order.side

            if not orders_can_match( # checks asset, side and makes sure buyer price >= seller price
                buy_order,
                sell_order
            ):
                break

            trade_quantity = min(
                buy_order.remaining_quantity,
                sell_order.remaining_quantity
            )

            execution_price = determine_execution_price(
                resting_order=resting_order,
                incoming_order=incoming_order
            )

            trade = Trade(
                trade_id=self.next_trade_id,
                resting_side=resting_side,

                buy_order_id=buy_order.order_id,
                sell_order_id=sell_order.order_id,

                buyer_trader_id=buy_order.trader_id,
                seller_trader_id=sell_order.trader_id,

                price=execution_price,
                quantity=trade_quantity,
                asset = buy_order.asset,

                timestamp=datetime.now()
            )

            self.next_trade_id += 1

            buy_order.remaining_quantity -= trade_quantity
            sell_order.remaining_quantity -= trade_quantity

            self.last_trade_price[incoming_order.asset] = execution_price

            self.record_trade(trade)
            new_trades.append(trade)

            if buy_order.remaining_quantity == 0:

                buy_order.status = OrderStatus.FILLED
                changed_orders[buy_order.order_id] = buy_order

                if buy_order is not incoming_order:
                    self.order_book.remove_order(
                        buy_order.order_id
                    )

            else:

                buy_order.status = (
                    OrderStatus.PARTIALLY_FILLED  # resting order status change
                )
                changed_orders[buy_order.order_id] = buy_order


            if sell_order.remaining_quantity == 0:

                sell_order.status = OrderStatus.FILLED
                changed_orders[sell_order.order_id] = sell_order

                if sell_order is not incoming_order:
                    self.order_book.remove_order(
                        sell_order.order_id
                    )

            else:

                sell_order.status = (
                    OrderStatus.PARTIALLY_FILLED   # resting order status change
                )
                changed_orders[sell_order.order_id] = sell_order

        if incoming_order.remaining_quantity > 0:  # After all the transactions/trading of the incoming market order, it gets added to the book as cancelled

            if incoming_order.order_type == OrderType.MARKET:
                    incoming_order.status = OrderStatus.CANCELLED
                    changed_orders[incoming_order.order_id] = incoming_order

            else:
                incoming_order.status = OrderStatus.ACTIVE
                self.order_book.add_order(incoming_order)


        return ExchangeResult(
            changed_orders=list(changed_orders.values()),
            trades=new_trades
        )

    def record_trade(self, trade: Trade):
        self.trade_history.append(trade)

    def record_orders(self, order: Order): # eventually remove this or revamp this into an updating registry instead of snapshots of submitted orders.
        self.submitted_orders[order.order_id] = deepcopy(order)






# =========================
# EXCHANGE RULES
# =========================

def validate_order(order: Order) -> bool:
    """
    Validates whether an order is legal before entering the exchange.
    """

    if not order.asset:
        return False

    if order.quantity <= 0:
        return False

    if order.remaining_quantity < 0:
        return False

    if order.remaining_quantity > order.quantity:
        return False

    if order.order_type == OrderType.LIMIT:

        if order.price is None:
            return False

        if order.price <= 0:
            return False

    elif order.order_type == OrderType.MARKET:

        if order.price is not None:
            return False

    return True


def orders_can_match(
    buy_order: Order,
    sell_order: Order
) -> bool:
    """
    Determines whether two orders are eligible to trade.
    """

    if buy_order.side != Side.BUY:
        return False

    if sell_order.side != Side.SELL:
        return False

    if buy_order.asset != sell_order.asset:
        return False

    # Fully filled orders cannot trade
    if buy_order.remaining_quantity <= 0:
        return False

    if sell_order.remaining_quantity <= 0:
        return False

    # Market order always accepts available liquidity
    if buy_order.order_type == OrderType.MARKET:
        return True

    if sell_order.order_type == OrderType.MARKET:
        return True

    # Limit price crossing condition
    return buy_order.price >= sell_order.price


def determine_execution_price(
    resting_order: Order,
    incoming_order: Order
    ):

    return resting_order.price


# =========================
# TEST OBJECT CREATION
# =========================

if __name__ == "__main__":

    from time import sleep

    exchange = Exchange(reference_price=10000)

    sell_order_1 = Order(
        trader_id=101,
        timestamp=datetime.now(),

        side=Side.SELL,
        order_type=OrderType.LIMIT,

        price=10000,
        asset="BTC",

        quantity=5,
        remaining_quantity=5,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(sell_order_1)

    sleep(1)

    sell_order_2 = Order(
        trader_id=102,
        timestamp=datetime.now(),

        side=Side.SELL,
        order_type=OrderType.LIMIT,

        price=10100,
        asset="BTC",

        quantity=5,
        remaining_quantity=5,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(sell_order_2)

    sell_order_3 = Order(
        trader_id=104,
        timestamp=datetime.now(),

        side=Side.SELL,
        order_type=OrderType.LIMIT,

        price=10200,
        asset="BTC",

        quantity=5,
        remaining_quantity=5,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(sell_order_3)


    buy_order = Order(
        trader_id=103,
        timestamp=datetime.now(),

        side=Side.BUY,
        order_type=OrderType.MARKET,

        price=None,
        asset="BTC",

        quantity=12,
        remaining_quantity=12,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(buy_order)

    print("\nTrade History:")
    for trade in exchange.trade_history:
        print(trade)

    print("\nSell Order 1:")
    print(sell_order_1.status)
    print(sell_order_1.remaining_quantity)

    print("\nSell Order 2:")
    print(sell_order_2.status)
    print(sell_order_2.remaining_quantity)

    print("\nBook:")
    print(exchange.order_book.asks)
    
   