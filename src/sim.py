from time import perf_counter
import random
from src.core import Exchange
from src.traders.trader import RandomTrader
from src.analysis import analyze_simulation
from src.core import (
    Exchange,
    OrderStatus,
    OrderType,
)

random.seed(42)

NUM_TRADERS = 50
NUM_SUBMISSIONS = 100_000


exchange = Exchange(
    reference_price=10000
)


traders = [
    RandomTrader(
        trader_id=i,
        cash=1_000_000,
        inventory={
            "BTC": 0,
            "ETH": 0
        }
    )
    for i in range(1, NUM_TRADERS + 1)
]

def run_simulation(
    exchange,
    traders,
    num_submissions,
):

    trader_lookup = {
        trader.trader_id: trader
        for trader in traders
    }

    for _ in range(num_submissions):

        trader = random.choice(traders)

        order = trader.step(exchange)

        if order is None:
            continue

        changed_orders = exchange.submit_order(order)

        if order.status in (
            OrderStatus.ACTIVE,
            OrderStatus.PARTIALLY_FILLED,
        ):
            trader.active_orders[
                order.order_id
            ] = order

        for changed_order in changed_orders:

            owner = trader_lookup[
                changed_order.trader_id
            ]

            if changed_order.status in (
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
            ):

                owner.active_orders.pop(
                    changed_order.order_id,
                    None
                )


start = perf_counter()

run_simulation(
    exchange,
    traders,
    NUM_SUBMISSIONS
)

end = perf_counter()

runtime = end - start

analyze_simulation(
    exchange,
    traders,
    runtime
)
