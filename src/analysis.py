from src.core import OrderStatus, OrderType

ASSETS = ("BTC", "ETH")


def analyze_simulation(
    exchange,
    traders,
    runtime,
):

    # ==========================
    # MARKET
    # ==========================

    total_volume = sum(
        trade.quantity
        for trade in exchange.trade_history
    )

    submitted = len(
        exchange.submitted_orders
    )

    orders_per_second = (
        submitted / runtime
    )

    average_trade_size = (
        total_volume / len(exchange.trade_history)
        if exchange.trade_history
        else 0
    )

    # ============================
    # LIQUIDITY
    # ============================

    fill_rate = (
        len(exchange.trade_history)
        / submitted
    )

    largest_trade = max(
        (trade.quantity for trade in exchange.trade_history),
        default=0
    )

    smallest_trade = min(
        (trade.quantity for trade in exchange.trade_history),
        default=0
    )

    avg_active_orders = (
        sum(
            len(trader.active_orders)
            for trader in traders
        )
        / len(traders)
    )   


    # ============================
    # PORTFOLIO
    # ============================


    reserved_cash = sum(
        trader.portfolio.reserved_cash
        for trader in traders
    )

    reserved_inventory = {
        asset: sum(
            trader.portfolio.reserved_inventory.get(asset, 0)
            for trader in traders
        )
        for asset in ASSETS
    }


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

    all_tests_passed = all([
        filled_in_book == 0,
        cancelled_in_book == 0,
        negative_qty == 0,
        overfilled_orders == 0,
        market_orders_in_book == 0,
        zero_qty_orders == 0,
    ])

    # ==========================
    # REPORT
    # ==========================

    print("\n====  REPORT ====")
    print()

    print(f"Volume: {total_volume}")
    print(f"Trades: {len(exchange.trade_history)}")
    print(f"Submitted Orders: {submitted}")
    print(f"Fill Rate: {fill_rate:.2%}")
    print(f"largest trade: {largest_trade}")
    print(f"smallest trade: {smallest_trade}")
    print(f"reserved cash: {reserved_cash}")
    for asset in ASSETS:
        print(
            f"Reserved {asset}: "
            f"{reserved_inventory[asset]}"
        )
    print(f"Average Active Orders across all traders: {avg_active_orders}")
    print(
        f"Active Orders In Book: "
        f"{len(exchange.order_book.order_lookup)}"
    )

    print()

    for asset in ASSETS:

        best_bid = exchange.order_book.get_best_bid(asset)
        best_ask = exchange.order_book.get_best_ask(asset)

        spread = None

        if (
            best_bid is not None
            and best_ask is not None
        ):
            spread = best_ask - best_bid

        asset_volume = sum(
            trade.quantity
            for trade in exchange.trade_history
            if trade.asset == asset
        )

        asset_trades = [
            trade
            for trade in exchange.trade_history
            if trade.asset == asset
        ]

        if asset_volume > 0:

            vwap = (
                sum(
                    trade.price * trade.quantity
                    for trade in asset_trades
                )
                / asset_volume
            )

        else:
            vwap = None

        print(f"--- {asset} ---")
        print(
            f"Last Trade Price: "
            f"{exchange.last_trade_price[asset]}"
        )
        print(f"Volume: {asset_volume}")
        print(f"Trades: {len(asset_trades)}")
        print(f"Best Bid: {best_bid}")
        print(f"Best Ask: {best_ask}")
        print(f"Spread: {spread}")
        print(f"VWAP: {vwap}")
        print()

    print("=== PERFORMANCE ===")

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

    print()
    print("\n=== TEST RESULT ===")

    return all_tests_passed