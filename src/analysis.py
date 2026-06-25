from src.core import OrderStatus, OrderType


def analyze_simulation(
    exchange,
    traders,
    runtime,
):

    # ==========================
    # MARKET STATS
    # ==========================

    total_volume = sum(
        trade.quantity
        for trade in exchange.trade_history
    )

    best_bid = exchange.order_book.get_best_bid()
    best_ask = exchange.order_book.get_best_ask()

    spread = None

    if (
        best_bid is not None
        and best_ask is not None
    ):
        spread = best_ask - best_bid

    # ==========================
    # INVARIANT CHECKS
    # ==========================

    filled_in_book = 0
    cancelled_in_book = 0
    negative_qty = 0
    overfilled_orders = 0
    market_orders_in_book = 0
    zero_qty_orders = 0

    for order in exchange.order_book.order_lookup.values():

        if order.status == OrderStatus.FILLED:
            filled_in_book += 1

        if order.status == OrderStatus.CANCELLED:
            cancelled_in_book += 1

        if order.remaining_quantity < 0:
            negative_qty += 1

        if order.remaining_quantity > order.quantity:
            overfilled_orders += 1

        if order.order_type == OrderType.MARKET:
            market_orders_in_book += 1

        if order.remaining_quantity == 0:
            zero_qty_orders += 1

    # ==========================
    # PERFORMANCE
    # ==========================

    submitted = len(exchange.submitted_orders)

    orders_per_second = (
        submitted / runtime
    )

    # ==========================
    # REPORT
    # ==========================

    print("\n=== MARKET STATS ===")

    print(f"Volume: {total_volume}")
    print(f"Trades: {len(exchange.trade_history)}")
    print(f"Submitted Orders: {submitted}")

    print(
        f"Active Orders In Book: "
        f"{len(exchange.order_book.order_lookup)}"
    )

    print(
        f"Last Trade Price: "
        f"{exchange.last_trade_price}"
    )

    print(f"Best Bid: {best_bid}")
    print(f"Best Ask: {best_ask}")
    print(f"Spread: {spread}")

    print("\n=== PERFORMANCE ===")

    print(
        f"Runtime: {runtime:.4f} seconds"
    )

    print(
        f"Orders / Second: "
        f"{orders_per_second:,.0f}"
    )

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
        f"Remaining > Quantity: "
        f"{overfilled_orders}"
    )

    print(
        f"Market Orders In Book: "
        f"{market_orders_in_book}"
    )

    print(
        f"Zero Quantity Orders In Book: "
        f"{zero_qty_orders}"
    )

    all_tests_passed = all([
        filled_in_book == 0,
        cancelled_in_book == 0,
        negative_qty == 0,
        overfilled_orders == 0,
        market_orders_in_book == 0,
        zero_qty_orders == 0,
    ])

    print("\n=== Trader stats ===")
    for trader in traders:

        print(
            trader.trader_id,
            len(trader.active_orders)
        )

    print("\n=== VWAP ===")
    vwap = (
        sum(
            trade.price * trade.quantity
            for trade in exchange.trade_history
        )
        /
        total_volume
    )
    print(vwap)


    print("\n=== TEST RESULT ===")

    print(
        "PASS"
        if all_tests_passed
        else "FAIL"
    )