from src.core import Side

def test_side_enum():

    assert Side.BUY.value == "BUY"
    assert Side.SELL.value == "SELL"