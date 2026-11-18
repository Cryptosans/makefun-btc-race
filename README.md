[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/Cryptosans/makefun-btc-race/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/Cryptosans/makefun-btc-race/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

# makefun-btc-race

A trading bot for make.fun's **"Race a BTC trading bot live for 24 hours"** bounty. It trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute on-chain bars, starting with $1,000 of paper money, speaking the `agent-fun/bars-replay/v1` protocol.

## Strategy

One-minute cbBTC bars are mostly noise (1-minute return sd ≈ 6.7 bps) while a full-size round trip costs ≈ 36 bps in fees, slippage and pool impact — so the bot only trades when a real multi-hour move is under way:

- **Enter** (flat only): the 60-bar return is at least +25 bps **and** the 120-bar high–low range is at least 150 bps (volatility expansion). It buys with the full cash balance.
- **Exit**: an 80 bp trailing stop from the highest close since entry.
- **Late-day floor**: if it has never traded by bar 1200, a plain 60-bar momentum reading of +15 bps is enough to enter, so a quiet day still produces the one trade the guardrails require.

Long only, at most one position, deterministic integer arithmetic, standard library only. No network, no wall clock, no files outside the repo.

## Dev-window backtest

Faithful replay of the published dev window (fill at the next bar's open, 4 bps fee, 2 bps slippage, constant-product impact against the bar's open depth):

| Metric | Value |
| --- | --- |
| Net PnL | **+$13.27 USDC** |
| Trades | 2 (1 round trip) |
| Max drawdown | 0.97% |

## Run it

```sh
python3 main.py
```

The bot reads `agent-fun/bars-replay/v1` messages (hello, then one batch per minute, then done) on stdin and writes exactly one reply per batch on stdout. `vendor/makefun_bars.py` is the kit's protocol shim, vendored byte for byte.

<sub>Entered on [make.fun](https://make.fun/?ref=nstczpc4&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
