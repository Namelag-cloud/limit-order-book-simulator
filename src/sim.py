from time import perf_counter
import random

from src.analysis import analyze_simulation
from src.core import (
    Exchange,
    OrderStatus,
    OrderType,
    Side,
)
from src.traders.trader import (
    RandomTrader,
    Portfolio,
)

random.seed(42)

NUM_TRADERS = 10
NUM_SUBMISSIONS = 100_000


def make_portfolio() -> Portfolio:

    return Portfolio(
        cash=100_000,
        inventory={
            "BTC": 50,
            "ETH": 50,
        },
    )


exchange = Exchange(
    reference_price=10_000
)

traders = [
    RandomTrader(
        trader_id=i,
        portfolio=make_portfolio(),
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

        # ==========================
        # Trader Decision
        # ==========================

        trader = random.choice(traders)

        order = trader.step(exchange)

        if order is None:
            continue

        # ==========================
        # Exchange
        # ==========================

        result = exchange.submit_order(order)

        # ==========================
        # New Resting Limit Order
        # ==========================

        if (
            order.order_type == OrderType.LIMIT
            and order.status == OrderStatus.ACTIVE
        ):

            trader.active_orders[
                order.order_id
            ] = order

            if order.side == Side.BUY: # reserve cash or inventroy depending on the side.

                trader.portfolio.reserve_cash(
                    order.remaining_quantity
                    * order.price
                )

            else:

                trader.portfolio.reserve_inventory(
                    order.asset,
                    order.remaining_quantity
                )

        # ==========================
        # Trade Settlement
        # ==========================

        for trade in result.trades:

            buyer = trader_lookup[
                trade.buyer_trader_id
            ]

            seller = trader_lookup[
                trade.seller_trader_id
            ]

            # Portfolio settlement

            buyer.portfolio.buy(
                asset=trade.asset,
                quantity=trade.quantity,
                price=trade.price,
            )

            seller.portfolio.sell(
                asset=trade.asset,
                quantity=trade.quantity,
                price=trade.price,
            )

            # Release reservation from the RESTING limit order

            if trade.resting_side == Side.BUY:

                buyer.portfolio.release_cash(
                    trade.quantity
                    * trade.price
                )

            else:

                seller.portfolio.release_inventory(
                    trade.asset,
                    trade.quantity
                )

        # ==========================
        # Changed Orders
        # ==========================

        for changed_order in result.changed_orders:

            owner = trader_lookup[
                changed_order.trader_id
            ]

            if changed_order.status in (
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
            ):

                owner.active_orders.pop(
                    changed_order.order_id,
                    None,
                )

            # Release anything still reserved
            # when a resting LIMIT order is
            # cancelled.

            if (
                changed_order.status == OrderStatus.CANCELLED
                and changed_order.order_type == OrderType.LIMIT
            ):

                if changed_order.side == Side.BUY:

                    owner.portfolio.release_cash(
                        changed_order.remaining_quantity
                        * changed_order.price
                    )

                else:

                    owner.portfolio.release_inventory(
                        changed_order.asset,
                        changed_order.remaining_quantity
                    )


start = perf_counter()

run_simulation(
    exchange,
    traders,
    NUM_SUBMISSIONS,
)

runtime = perf_counter() - start

analyze_simulation(
    exchange,
    traders,
    runtime,
)

ASSETS = ("BTC", "ETH")

print("\n=== ENGINE INVARIANTS ===")

checks = []

# =====================================
# Portfolio Invariants
# =====================================

for trader in traders:

    p = trader.portfolio

    checks.append(p.cash >= 0)
    checks.append(p.reserved_cash >= 0)

    for asset in ASSETS:

        checks.append(
            p.inventory.get(asset, 0) >= 0
        )

        checks.append(
            p.reserved_inventory.get(asset, 0) >= 0
        )

        # Reserved inventory cannot exceed inventory

        checks.append(
            p.reserved_inventory.get(asset, 0)
            <=
            p.inventory.get(asset, 0)
        )

    # Reserved cash should never exceed cash

    checks.append(
        p.reserved_cash <= p.cash
    )

# =====================================
# Active Order Accounting
# =====================================

for trader in traders:

    reserved_cash = 0

    reserved_inventory = {
        asset: 0
        for asset in ASSETS
    }

    for order in trader.active_orders.values():

        assert order.status in (
            OrderStatus.ACTIVE,
            OrderStatus.PARTIALLY_FILLED,
        )

        if order.order_type != OrderType.LIMIT:
            continue

        if order.side == Side.BUY:

            reserved_cash += (
                order.remaining_quantity
                * order.price
            )

        else:

            reserved_inventory[
                order.asset
            ] += order.remaining_quantity

    checks.append(
        trader.portfolio.reserved_cash
        == reserved_cash
    )

    for asset in ASSETS:

        checks.append(
            trader.portfolio.reserved_inventory.get(asset, 0)
            ==
            reserved_inventory[asset]
        )

# =====================================
# Order Book Invariants
# =====================================

for asset in ASSETS:

    best_bid = exchange.order_book.get_best_bid(asset)
    best_ask = exchange.order_book.get_best_ask(asset)

    checks.append(
        best_bid is None
        or best_ask is None
        or best_bid < best_ask
    )

# =====================================
# Order Registry
# =====================================

for order in exchange.order_book.order_lookup.values():

    checks.append(
        order.status in (
            OrderStatus.ACTIVE,
            OrderStatus.PARTIALLY_FILLED,
        )
    )

    checks.append(
        order.remaining_quantity > 0
    )

# =====================================
# Conservation of Assets
# =====================================

for asset in ASSETS:

    total_inventory = sum(
        trader.portfolio.inventory.get(asset, 0)
        for trader in traders
    )

    checks.append(total_inventory == 50 * NUM_TRADERS)

# =====================================
# Conservation of Cash
# =====================================

checks.append(

    sum(
        trader.portfolio.cash
        for trader in traders
    )

    ==

    100_000 * NUM_TRADERS

)

print(
    "PASS"
    if all(checks)
    else "FAIL"
)