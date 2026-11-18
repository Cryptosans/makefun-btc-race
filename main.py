"""cbBTC trend bot for make.fun's "Race a BTC trading bot live for 24 hours".

Strategy (designed from the dev window's own statistics, no baseline code read):
  * 1-minute cbBTC/USDC bars are mostly noise (1-min return sd ~6.7 bps) while
    a full-size round trip costs ~36 bps, so the bot only trades when a real
    multi-hour move is under way: the 60-bar return is at least +25 bps AND
    the 120-bar high-low range is at least 180 bps (volatility expansion).
  * It buys the whole cash balance once, then rides the move with an 80 bp
    trailing stop measured from the highest close since entry.
  * If it has still never traded by bar 1200, a plain 60-bar momentum
    reading of +15 bps is enough to enter, so a quiet day still produces
    the one trade the guardrails require.
  * Long only, at most one position, deterministic integer arithmetic,
    no network, no clock, no files outside the repo.

Dev-window backtest (faithful replay: fill at next bar's open, 4 bps fee,
2 bps slippage, constant-product impact vs the bar's open depth):
net PnL +$13.27, 1 round trip, max drawdown 0.97%.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
MOM_W = 60            # momentum window, bars
MOM_MIN_BPS = 25      # 60-bar return needed to enter
RANGE_W = 120         # volatility-expansion window, bars
RANGE_MIN_BPS = 180   # 120-bar high-low range needed to enter (sweep5: 120/150/180
                      # bps all give the same dev PnL — the entry bars clear 180, so
                      # the tighter bound only filters weaker live moves)
TRAIL_BPS = 80        # trailing stop from the highest close since entry
FALLBACK_SEQ = 1200   # late-day participation floor
FALLBACK_MOM_BPS = 15
MAX_SLIP_BPS = 200    # generous cap vs the ~14 bp a normal fill moves


class Bot:
    def __init__(self):
        self.closes = []
        self.highs = []
        self.lows = []
        self.peak = None        # highest close since the entry decision
        self.pending_buy = False
        self.ever_held = False

    def on_batch(self, state, batch):
        for bar in batch.get("bars", []):
            if bar.get("symbol") != SYMBOL:
                continue
            self.closes.append(int(bar["c"]))
            self.highs.append(int(bar["h"]))
            self.lows.append(int(bar["l"]))
        if state.warming_up:
            return []
        n = len(self.closes)
        holding = SYMBOL in state.positions and state.positions[SYMBOL].qty > 0
        if holding:
            self.ever_held = True
            self.pending_buy = False
            close = self.closes[-1]
            if self.peak is None or close > self.peak:
                self.peak = close
            if (self.peak - close) * 10000 // close >= TRAIL_BPS:
                self.peak = None
                return [{"side": "sell", "symbol": SYMBOL,
                         "qty": state.positions[SYMBOL].qty,
                         "max_slippage_bps": MAX_SLIP_BPS}]
            return []
        if self.pending_buy:
            # The buy never filled (rejected): clear the entry state.
            self.pending_buy = False
            self.peak = None
        if n <= RANGE_W:
            return []
        close = self.closes[-1]
        mom_bps = (close - self.closes[-1 - MOM_W]) * 10000 // self.closes[-1 - MOM_W]
        fire = False
        if mom_bps >= MOM_MIN_BPS:
            hi = max(self.highs[-RANGE_W - 1:])
            lo = min(self.lows[-RANGE_W - 1:])
            if (hi - lo) * 10000 // close >= RANGE_MIN_BPS:
                fire = True
        if not fire and not self.ever_held and state.seq >= FALLBACK_SEQ \
                and mom_bps >= FALLBACK_MOM_BPS:
            fire = True
        if fire:
            self.peak = close
            self.pending_buy = True
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIP_BPS}]
        return []


def main():
    makefun_bars.run(Bot().on_batch)


if __name__ == "__main__":
    main()
