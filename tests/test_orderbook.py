
from datetime import datetime

from src.core import (
    Exchange,
    Order,
    Side,
    OrderType,
    OrderStatus,
)
from src.helper import make_limit_order


ASSET = "BTC"


def make_exchange() -> Exchange:
    return Exchange(reference_price=100)


def submit(exchange, *orders):
    for order in orders:
        exchange.submit_order(order)


def test_exact_fill():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
    trader_id=101,
    side=Side.SELL,
    price=100,
    quantity=5,
    asset=ASSET,
)   

    buy = make_limit_order(
    trader_id=102,
    side=Side.BUY,
    price=100,
    quantity=5,
    asset=ASSET,
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
        asset=ASSET
    ) 

    buy = make_limit_order(
    trader_id=102,
    side=Side.BUY,
    price=100,
    quantity=5,
    asset=ASSET,
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
    asset=ASSET,
) 

    sell2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=100,
        quantity=5,
        asset=ASSET
    ) 

    buy = make_limit_order(
        trader_id=103,
        side=Side.BUY,
        price=100,
        quantity=7,
        asset=ASSET
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
        asset=ASSET
    ) 

    buy = make_limit_order(
    trader_id=102,
    side=Side.BUY,
    price=100,
    quantity=5,
    asset=ASSET,
)

    exchange.submit_order(sell)
    exchange.submit_order(buy)

    assert len(exchange.trade_history) == 0

    assert sell.status == OrderStatus.ACTIVE
    assert buy.status == OrderStatus.ACTIVE

    assert exchange.order_book.get_best_ask(ASSET) == 101
    assert exchange.order_book.get_best_bid(ASSET) == 100

def test_book_sweep():

    exchange = Exchange(reference_price=100)

    sell1 = make_limit_order(
    trader_id=101,
    side=Side.SELL,
    price=100,
    quantity=5,
    asset=ASSET,
) 

    sell2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=101,
        quantity=5,
        asset=ASSET
    ) 

    buy = make_limit_order(
        trader_id=103,
        side=Side.BUY,
        price=101,
        quantity=10,
        asset=ASSET
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
    asset=ASSET,
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

    assert not exchange.order_book.asks[ASSET]

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
    asset=ASSET,
) 
    )

    exchange.submit_order(
        make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=101,
        quantity=5,
        asset=ASSET
    ) 
    )

    exchange.submit_order(
        make_limit_order(
        trader_id=103,
        side=Side.SELL,
        price=102,
        quantity=5,
        asset=ASSET
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

    assert exchange.order_book.get_best_ask(ASSET) == 102

    remaining_order = (
        exchange.order_book.asks[ASSET][102][0]
    )

    assert remaining_order.remaining_quantity == 3



def test_market_order_partial_fill():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
    trader_id=101,
    side=Side.SELL,
    price=100,
    quantity=5,
    asset=ASSET,
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
    asset=ASSET,
) 

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=105,
        quantity=5,
        asset=ASSET
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
    asset=ASSET,
) 

    sell2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=100,
        quantity=5,
        asset=ASSET
    ) 

    exchange.submit_order(sell1)
    exchange.submit_order(sell2)

    buy = make_limit_order(
        trader_id=103,
        side=Side.BUY,
        price=100,
        quantity=5,
        asset=ASSET
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
        quantity=1,
        asset=ASSET
    )

    order2 = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=101,
        quantity=1,
        asset=ASSET
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
        quantity=5,
        asset=ASSET,
    )

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    exchange.submit_order(sell)

    result = exchange.submit_order(buy)

    assert sell in result.changed_orders
    assert buy in result.changed_orders

    assert len(result.trades) == 1

def test_submit_order_returns_trades():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    exchange.submit_order(sell)

    result = exchange.submit_order(buy)

    assert len(result.trades) == 1

    trade = result.trades[0]

    assert trade.price == 100
    assert trade.quantity == 5
    assert trade.asset == ASSET


def test_trade_records_resting_sell_side():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=105,
        quantity=5,
        asset=ASSET,
    )

    exchange.submit_order(sell)

    result = exchange.submit_order(buy)

    trade = result.trades[0]

    assert trade.resting_side == Side.SELL


def test_trade_records_resting_buy_side():

    exchange = Exchange(reference_price=100)

    buy = make_limit_order(
        trader_id=101,
        side=Side.BUY,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    sell = make_limit_order(
        trader_id=102,
        side=Side.SELL,
        price=95,
        quantity=5,
        asset=ASSET,
    )

    exchange.submit_order(buy)

    result = exchange.submit_order(sell)

    trade = result.trades[0]

    assert trade.resting_side == Side.BUY


def test_trade_uses_exchange_assigned_order_ids():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    exchange.submit_order(sell)

    result = exchange.submit_order(buy)

    trade = result.trades[0]

    assert trade.buy_order_id == buy.order_id
    assert trade.sell_order_id == sell.order_id


def test_submit_order_returns_no_trades_when_orders_do_not_cross():

    exchange = Exchange(reference_price=100)

    sell = make_limit_order(
        trader_id=101,
        side=Side.SELL,
        price=101,
        quantity=5,
        asset=ASSET,
    )

    buy = make_limit_order(
        trader_id=102,
        side=Side.BUY,
        price=100,
        quantity=5,
        asset=ASSET,
    )

    exchange.submit_order(sell)

    result = exchange.submit_order(buy)

    assert result.trades == []


