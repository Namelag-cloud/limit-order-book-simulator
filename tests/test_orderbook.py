

from src.core import *
from src.helper import make_limit_order


def test_exact_fill():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        1, 101, Side.SELL, 100, 5
    )

    buy = make_limit_order(
        2, 102, Side.BUY, 100, 5
    )

    exchange.submit_order(sell)
    exchange.submit_order(buy)

    assert sell.status == OrderStatus.FILLED
    assert buy.status == OrderStatus.FILLED

    assert sell.remaining_quantity == 0
    assert buy.remaining_quantity == 0

    assert len(exchange.trade_history) == 1



def test_partial_fill():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        1, 101, Side.SELL, 100, 10
    )

    buy = make_limit_order(
        2, 102, Side.BUY, 100, 5
    )

    exchange.submit_order(sell)
    exchange.submit_order(buy)

    assert buy.status == OrderStatus.FILLED

    assert sell.status == (
        OrderStatus.PARTIALLY_FILLED
    )

    assert sell.remaining_quantity == 5

    assert len(exchange.trade_history) == 1




def test_price_time_priority():

    exchange = Exchange(reference_price=100)

    sell1 = make_limit_order(
        1, 101, Side.SELL, 100, 5
    )

    sell2 = make_limit_order(
        2, 102, Side.SELL, 100, 5
    )

    buy = make_limit_order(
        3, 103, Side.BUY, 100, 7
    )

    exchange.submit_order(sell1)
    exchange.submit_order(sell2)
    exchange.submit_order(buy)

    assert sell1.status == OrderStatus.FILLED

    assert sell2.status == (
        OrderStatus.PARTIALLY_FILLED
    )

    assert sell2.remaining_quantity == 3


def test_no_match():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        1, 101, Side.SELL, 101, 5
    )

    buy = make_limit_order(
        2, 102, Side.BUY, 100, 5
    )

    exchange.submit_order(sell)
    exchange.submit_order(buy)

    assert len(exchange.trade_history) == 0

    assert sell.status == OrderStatus.ACTIVE
    assert buy.status == OrderStatus.ACTIVE

    assert exchange.order_book.get_best_ask() == 101
    assert exchange.order_book.get_best_bid() == 100

def test_book_sweep():

    exchange = Exchange(reference_price=100)

    sell1 = make_limit_order(
        1, 101, Side.SELL, 100, 5
    )

    sell2 = make_limit_order(
        2, 102, Side.SELL, 101, 5
    )

    buy = make_limit_order(
        3, 103, Side.BUY, 101, 10
    )

    exchange.submit_order(sell1)
    exchange.submit_order(sell2)
    exchange.submit_order(buy)

    assert sell1.status == OrderStatus.FILLED
    assert sell2.status == OrderStatus.FILLED
    assert buy.status == OrderStatus.FILLED

    assert len(exchange.trade_history) == 2


def test_market_order_empty_book():

    exchange = Exchange(reference_price=100)

    market_buy = Order(
        order_id=1,
        trader_id=101,
        timestamp=datetime.now(),

        side=Side.BUY,
        order_type=OrderType.MARKET,

        price=None,
        asset="BTC",

        quantity=5,
        remaining_quantity=5,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(market_buy)

    assert market_buy.status == OrderStatus.CANCELLED

    assert len(exchange.trade_history) == 0


def test_cancel_order():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        1, 101, Side.SELL, 100, 5
    )

    exchange.submit_order(sell)

    result = exchange.cancel_order(
        sell.order_id
    )

    assert result is True

    assert sell.status == OrderStatus.CANCELLED

    assert sell.order_id not in (
        exchange.order_book.order_lookup
    )

    assert not exchange.order_book.asks

def test_cancel_nonexistent_order():

    exchange = Exchange(reference_price=100)

    result = exchange.cancel_order(999999)

    assert result is False


    