
from datetime import datetime

from src.core import (
    Exchange,
    Order,
    Side,
    OrderType,
    OrderStatus,
)
from src.helper import make_limit_order


def test_exact_fill():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    )   

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
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
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=10,
    ) 

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
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
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    sell2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    buy = make_limit_order(
        trader_id=103,
        side=Side.BUY,
        price=100,
        quantity=7,
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
        trader_id=101,
        side=Side.SELL,
        price=101,
        quantity=5,
    ) 

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
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
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    sell2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=101,
        quantity=5,
    ) 

    buy = make_limit_order(
        trader_id=103,
        side=Side.BUY,
        price=101,
        quantity=10,
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
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
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


def test_market_order_sweeps_multiple_levels():

    exchange = Exchange(reference_price=100)

    exchange.submit_order(
        make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 
    )

    exchange.submit_order(
        make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=101,
        quantity=5,
    ) 
    )

    exchange.submit_order(
        make_limit_order(
        trader_id=103,
        side=Side.SELL,
        price=102,
        quantity=5,
    ) 
    )

    market_buy = Order(
        trader_id=104,
        timestamp=datetime.now(),

        side=Side.BUY,
        order_type=OrderType.MARKET,

        price=None,
        asset="BTC",

        quantity=12,
        remaining_quantity=12,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(market_buy)

    assert len(exchange.trade_history) == 3

    assert exchange.order_book.get_best_ask() == 102

    remaining_order = (
        exchange.order_book.asks[102][0]
    )

    assert remaining_order.remaining_quantity == 3



def test_market_order_partial_fill():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    exchange.submit_order(sell)

    market_buy = Order(
        trader_id=102,
        timestamp=datetime.now(),

        side=Side.BUY,
        order_type=OrderType.MARKET,

        price=None,
        asset="BTC",

        quantity=10,
        remaining_quantity=10,

        status=OrderStatus.ACTIVE
    )

    exchange.submit_order(market_buy)

    assert sell.status == OrderStatus.FILLED

    assert market_buy.status == OrderStatus.CANCELLED

    assert market_buy.remaining_quantity == 5

    assert len(exchange.trade_history) == 1


def test_trade_executes_at_resting_price():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=105,
        quantity=5,
    )

    exchange.submit_order(sell)
    exchange.submit_order(buy)

    trade = exchange.trade_history[0]

    assert trade.price == 100



def test_fifo_same_price_level():

    exchange = Exchange(reference_price=100)

    sell1 = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    sell2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=100,
        quantity=5,
    ) 

    exchange.submit_order(sell1)
    exchange.submit_order(sell2)

    buy = make_limit_order(
        trader_id=103,
        side=Side.BUY,
        price=100,
        quantity=5,
    )

    exchange.submit_order(buy)

    assert sell1.status == OrderStatus.FILLED

    assert sell2.status == OrderStatus.ACTIVE

    assert sell2.remaining_quantity == 5


def test_market_order_never_rests():

    exchange = Exchange(reference_price=100)

    market_buy = Order(
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

    assert (
        market_buy.order_id
        not in exchange.order_book.order_lookup
    )



def test_exchange_assigns_order_ids():

    exchange = Exchange(reference_price=100)

    order1 = make_limit_order(
        trader_id=101,
        side=Side.BUY,
        price=100,
        quantity=1
    )

    order2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=101,
        quantity=1
    )

    assert order1.order_id is None
    assert order2.order_id is None

    exchange.submit_order(order1)
    exchange.submit_order(order2)

    assert order1.order_id == 1
    assert order2.order_id == 2

    assert exchange.next_order_id == 3





def test_submit_order_returns_changed_orders():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5
    )

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5
    )

    exchange.submit_order(sell)

    changed_orders = exchange.submit_order(buy)

    assert sell in changed_orders
    assert buy in changed_orders



