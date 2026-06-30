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




def make_portfolio(
    cash: int,
    inventory: int,
) -> Portfolio:

    return Portfolio(
        cash=cash,
        inventory={
            "BTC": inventory,
            "ETH": inventory,
        },
    )


EXPERIMENTS = [

    {
        "name": "Baseline",
        "num_traders": 10,
        "cash": 100_000,
        "inventory": 50,
        "submissions": 100_000,
    },

    {
        "name": "More Traders",
        "num_traders": 100,
        "cash": 100_000,
        "inventory": 50,
        "submissions": 100_000,
    },

    {
        "name": "Low Inventory",
        "num_traders": 10,
        "cash": 100_000,
        "inventory": 5,
        "submissions": 100_000,
    },

    {
        "name": "High Inventory",
        "num_traders": 10,
        "cash": 100_000,
        "inventory": 500,
        "submissions": 100_000,
    },

    {
        "name": "Low Cash",
        "num_traders": 10,
        "cash": 10_000,
        "inventory": 50,
        "submissions": 100_000,
    },

    {
        "name": "High Cash",
        "num_traders": 10,
        "cash": 1_000_000,
        "inventory": 50,
        "submissions": 100_000,
    },

    {
        "name": "1 Million Orders",
        "num_traders": 10,
        "cash": 100_000,
        "inventory": 50,
        "submissions": 1_000_000,
    },

    {
        "name": "5 Million Orders",
        "num_traders": 10,
        "cash": 100_000,
        "inventory": 50,
        "submissions": 5_000_000,
    },

    {
    "name": "Baseline Repeat",
    "num_traders": 10,
    "cash": 100_000,
    "inventory": 50,
    "submissions": 100_000,
    },
]


def run_simulation(
    num_traders,
    initial_cash,
    initial_inventory,
    num_submissions,
):

    traders = [
        RandomTrader(
            trader_id=i,
            portfolio=make_portfolio(
                initial_cash, 
                initial_inventory
            ),
        )
        for i in range(1, num_traders + 1)
    ]

    trader_lookup = {
        trader.trader_id: trader
        for trader in traders
    }

    exchange = Exchange(
        reference_price=10_000
    )

    iterations_without_order = 0

    for _ in range(num_submissions):

        # ==========================
        # Trader Decision
        # ==========================

        trader = random.choice(traders)

        action = trader.step(exchange)

        if action is None:
            iterations_without_order += 1
            continue

        elif isinstance(action, int):
            result = exchange.cancel_order(action) # cancel_order takes order_id 
        
        else:
            order = action
            result = exchange.submit_order(action) # this accepts the actual trade object

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

        
        for trader in traders:
            for order_id in trader.active_orders:

                assert (
                    order_id
                    in exchange.order_book.order_lookup
                )
                    


    return exchange, traders, iterations_without_order

summary = []

for experiment in EXPERIMENTS:

    random.seed(42)

    print("\n" + "=" * 80)
    print(f"EXPERIMENT: {experiment['name']}")
    print("=" * 80)

    print(
        f"""
Traders      : {experiment['num_traders']}
Cash         : {experiment['cash']}
Inventory    : {experiment['inventory']}
Submissions  : {experiment['submissions']}
"""
    )

    start = perf_counter()

    exchange, traders, iterations_without_order = run_simulation(
        num_traders=experiment["num_traders"],
        initial_cash=experiment["cash"],
        initial_inventory=experiment["inventory"],
        num_submissions=experiment["submissions"],
    )

    runtime = perf_counter() - start

    passed = analyze_simulation(
        exchange,
        traders,
        runtime,
    )

    summary.append({
        "Experiment": experiment["name"],
        "Runtime": runtime,
        "Orders": experiment["submissions"],
        "No Order": iterations_without_order,
        "PASS": passed,
    })


print("\n")
print("=" * 100)
print("SUMMARY")
print("=" * 100)

for result in summary:

    print(
        f"{result['Experiment']:<25}"
        f"{result['Orders']:<12,}"
        f"{result['Runtime']:<10.2f}"
        f"{'PASS' if result['PASS'] else 'FAIL':<12}"
        f"{result['No Order']:<15}"
    )