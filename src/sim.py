from src.core import Exchange
from src.helper import RandomOrderGenerator
import random
from time import perf_counter
from src.core import (
    Order,
    Side,
    OrderType,
    OrderStatus
)


start = perf_counter()

exchange = Exchange(
    reference_price=10000
)

generator = RandomOrderGenerator(
    reference_price=10000,
    market_order_probability=1.0
)

for i in range(10_000):

    order = generator.generate(
        order_id=i,
        trader_id=random.randint(1, 50)
    )

    exchange.submit_order(order)


end = perf_counter()

total_volume = sum(
    trade.quantity
    for trade in exchange.trade_history
)

# ==========================
# INVARIANT TESTS
# ==========================

filled_in_book = 0
cancelled_in_book = 0
negative_qty = 0
overfilled_orders = 0

for order in exchange.order_book.order_lookup.values():

    if order.status == OrderStatus.FILLED:
        filled_in_book += 1

    if order.status == OrderStatus.CANCELLED:
        cancelled_in_book += 1

    if order.remaining_quantity < 0:
        negative_qty += 1

    if order.remaining_quantity > order.quantity:
        overfilled_orders += 1

market_orders_in_book = 0

for order in exchange.order_book.order_lookup.values():

    if order.order_type == OrderType.MARKET:
        market_orders_in_book += 1

print(
    f"Market Orders In Book: "
    f"{market_orders_in_book}"
)

# ==========================
# BOOK STATS
# ==========================

best_bid = exchange.order_book.get_best_bid()
best_ask = exchange.order_book.get_best_ask()

spread = None

if (
    best_bid is not None
    and best_ask is not None
):
    spread = best_ask - best_bid


# ==========================
# ORDER STATUS STATS
# ==========================

active = 0
partial = 0
filled = 0
cancelled = 0

for order in exchange.submitted_orders.values():

    match order.status:

        case OrderStatus.ACTIVE:
            active += 1

        case OrderStatus.PARTIALLY_FILLED:
            partial += 1

        case OrderStatus.FILLED:
            filled += 1

        case OrderStatus.CANCELLED:
            cancelled += 1


# ==========================
# PERFORMANCE
# ==========================

runtime = end - start

orders_per_second = (
    len(exchange.submitted_orders)
    / runtime
)


# ==========================
# REPORT
# ==========================

print("\n=== MARKET STATS ===")

print(f"Volume: {total_volume}")
print(f"Trades: {len(exchange.trade_history)}")

print(
    f"Active Orders In Book: "
    f"{len(exchange.order_book.order_lookup)}"
)

print(
    f"Submitted Orders: "
    f"{len(exchange.submitted_orders)}"
)

print(
    f"Last Trade Price: "
    f"{exchange.last_trade_price}"
)

print(f"Best Bid: {best_bid}")
print(f"Best Ask: {best_ask}")
print(f"Spread: {spread}")


print("\n=== ORDER STATUS ===")

print(f"ACTIVE: {active}")
print(f"PARTIALLY_FILLED: {partial}")
print(f"FILLED: {filled}")
print(f"CANCELLED: {cancelled}")


print("\n=== INVARIANT CHECKS ===")

print(
    f"Filled Orders In Book: "
    f"{filled_in_book}"
)

print(
    f"Cancelled Orders In Book: "
    f"{cancelled_in_book}"
)

print(
    f"Negative Quantities: "
    f"{negative_qty}"
)

print(
    f"Remaining > Original Qty: "
    f"{overfilled_orders}"
)


print("\n=== PERFORMANCE ===")

print(
    f"Runtime: "
    f"{runtime:.4f} seconds"
)

print(
    f"Orders / Second: "
    f"{orders_per_second:,.0f}"
)


all_tests_passed = (
    filled_in_book == 0
    and cancelled_in_book == 0
    and negative_qty == 0
    and overfilled_orders == 0
)

print("\n=== TEST RESULT ===")

if all_tests_passed:
    print("PASS")
else:
    print("FAIL")

for order in exchange.order_book.order_lookup.values():

    if order.remaining_quantity == 0:
        print("BUG")


