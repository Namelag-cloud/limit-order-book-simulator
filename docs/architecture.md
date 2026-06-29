# Architecture

## Goal

Build a realistic event-driven exchange simulator for
research into market microstructure.

---

## Components

OrderBook
Exchange
Trader
Trade Settlement
Analytics
Simulation

---

## Design Philosophy

The exchange should only enforce exchange rules.

Trading strategies should live entirely inside
Trader subclasses.

Settlement is separated from matching to keep the
exchange deterministic and reusable.

Portfolio accounting is isolated from trader logic.