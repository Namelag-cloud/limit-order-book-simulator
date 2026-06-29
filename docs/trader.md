# Trader API

Every trader implements

step(exchange) which returns orders.

The trader may

- inspect market state (future addition, exclusive to certain trader types.)
- cancel orders (only for certain traders.)
- submit new orders (everyone)

The trader never modifies the exchange directly.

The exchange remains the source of truth.