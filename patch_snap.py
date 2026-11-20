#!/usr/bin/env python3
"""Independent snap lane: second break of a 3s burst, fixed target, then out."""
import os
import shutil
import py_compile

TARGET = "main.py"
BACKUP = "main.py.bak_snap"

PAIRS = [
(
'''    IMPULSE_BLOCK_MINUTES = 20.0
''',
'''    IMPULSE_BLOCK_MINUTES = 20.0
    # Snap: same burst the jump sees, but it waits for a pullback and a second break.
    # It banks a fixed target and leaves. It does not trail and it does not use the jump seat.
    ENABLE_SNAP = True
    SNAP_MAX_POSITIONS = 1
    SNAP_RISK = 0.0010
    SNAP_TARGET_R = 0.70
    SNAP_MAX_HOLD_SEC = 75.0
    SNAP_WINDOW_SEC = 25.0
    SNAP_PULL_MIN = 0.25
    SNAP_PULL_MAX = 0.55
    SNAP_MAX_SPREAD = 0.0012
    SNAP_MIN_DEPTH = 400.0
'''
),
(
'''    if trade.get("daily_carry"):
        return "daily"
    if trade.get("impulse"):
''',
'''    if trade.get("daily_carry"):
        return "daily"
    if trade.get("snap"):
        return "snap"
    if trade.get("impulse"):
'''
),
(
'''    """At peak +1.00R park the stop at +0.40R. The +1.50R ratchet still follows after that."""
    if trade.get("r1_locked") or trade.get("trailing_activated"):
''',
'''    """At peak +1.00R park the stop at +0.40R. The +1.50R ratchet still follows after that."""
    if trade.get("snap"):
        return
    if trade.get("r1_locked") or trade.get("trailing_activated"):
'''
),
(
'''    """At +$0.50 open profit, park the stop at entry. Does not override a +0.25R winner lock."""
    if trade.get("dollar_be") or trade.get("breakeven_moved") or trade.get("trailing_activated"):
''',
'''    """At +$0.50 open profit, park the stop at entry. Does not override a +0.25R winner lock."""
    if trade.get("snap"):
        return
    if trade.get("dollar_be") or trade.get("breakeven_moved") or trade.get("trailing_activated"):
'''
),
(
'''    """At +0.50R park the exchange stop at +0.25R. A prior entry lock may be raised, never lowered."""
    if trade.get("profit_locked") or trade.get("trailing_activated") or trade.get("ld_early_lock") or trade.get("r1_locked"):
''',
'''    """At +0.50R park the exchange stop at +0.25R. A prior entry lock may be raised, never lowered."""
    if trade.get("snap"):
        return
    if trade.get("profit_locked") or trade.get("trailing_activated") or trade.get("ld_early_lock") or trade.get("r1_locked"):
'''
),
(
'''    """Once peak >= 1R, walk the exchange stop up. Never lower it. UNI 1.55→0.35 fix."""
    start = float(getattr(config, "RATCHET_START_R", 1.0))
''',
'''    """Once peak >= 1R, walk the exchange stop up. Never lower it. UNI 1.55→0.35 fix."""
    if trade.get("snap"):
        return
    start = float(getattr(config, "RATCHET_START_R", 1.0))
'''
),
(
'''                elif (quality_report or {}).get("daily_carry"):
                    risk = float(getattr(config, "DAILY_CARRY_RISK", 0.004))
''',
'''                elif (quality_report or {}).get("daily_carry"):
                    risk = float(getattr(config, "DAILY_CARRY_RISK", 0.004))
                elif (quality_report or {}).get("snap"):
                    risk = float(getattr(config, "SNAP_RISK", 0.0010))
'''
),
(
'''            if (quality_report or {}).get("impulse") and stop_dist > 0 and equity > 0:
                target_usd = equity * float(getattr(config, "IMPULSE_RISK", 0.0025))
                sized = await adjust_quantity(symbol, target_usd / stop_dist)
                if sized <= 0 or sized * stop_dist > equity * 0.0035:
                    logger.info(f"🚫 IMPULSE size {symbol} | target=${target_usd:.2f}")
                    active_trades[strategy_name].pop(symbol, None)
                    return False
                qty = sized
''',
'''            if (quality_report or {}).get("impulse") and stop_dist > 0 and equity > 0:
                target_usd = equity * float(getattr(config, "IMPULSE_RISK", 0.0025))
                sized = await adjust_quantity(symbol, target_usd / stop_dist)
                if sized <= 0 or sized * stop_dist > equity * 0.0035:
                    logger.info(f"🚫 IMPULSE size {symbol} | target=${target_usd:.2f}")
                    active_trades[strategy_name].pop(symbol, None)
                    return False
                qty = sized

            if (quality_report or {}).get("snap") and stop_dist > 0 and equity > 0:
                target_usd = equity * float(getattr(config, "SNAP_RISK", 0.0010))
                sized = await adjust_quantity(symbol, target_usd / stop_dist)
                if sized <= 0 or sized * stop_dist > equity * 0.0015:
                    logger.info(f"🚫 SNAP size {symbol} | target=${target_usd:.2f}")
                    active_trades[strategy_name].pop(symbol, None)
                    return False
                qty = sized
'''
),
(
'''                logger.info(f"✅ SL accepted by exchange on {symbol} (orderId={sl_order.get('orderId', '?')}) — skip aggressive force-close")
''',
'''                logger.info(f"✅ SL accepted by exchange on {symbol} (orderId={sl_order.get('orderId', '?')}) — skip aggressive force-close")
                if (quality_report or {}).get("snap") and stop_dist > 0 and qty > 0:
                    tgt_r = float(getattr(config, "SNAP_TARGET_R", 0.70))
                    tgt = entry_price + stop_dist * tgt_r if side == "BUY" else entry_price - stop_dist * tgt_r
                    try:
                        tp_px = await adjust_price(tgt, symbol)
                        tp_qty = await adjust_quantity(symbol, qty)
                        if tp_qty > 0 and tp_px > 0:
                            tp_order = await client.futures_create_order(
                                symbol=symbol,
                                side="SELL" if side == "BUY" else "BUY",
                                type="TAKE_PROFIT_MARKET",
                                stopPrice=tp_px,
                                quantity=tp_qty,
                                reduceOnly=True,
                                workingType="CONTRACT_PRICE",
                            )
                            if tp_order:
                                logger.info(f"🎯 SNAP target {symbol} @ {tp_px} | +{tgt_r:.2f}R")
                    except Exception as e:
                        logger.warning(f"SNAP target failed {symbol} | stop left live | {e}")
'''
),
(
'''                "daily_carry": bool((quality_report or {}).get("daily_carry")),
''',
'''                "daily_carry": bool((quality_report or {}).get("daily_carry")),
                "snap": bool((quality_report or {}).get("snap")),
'''
),
(
'''            trade_label = "DailyCarry" if (quality_report or {}).get("daily_carry") else strategy_name
''',
'''            if (quality_report or {}).get("daily_carry"):
                trade_label = "DailyCarry"
            elif (quality_report or {}).get("snap"):
                trade_label = "Snap"
            else:
                trade_label = strategy_name
'''
),
(
'''                        hard_hit = impulse_hard_confirmed(symbol, trade, current_r)
                        if usd_loss_hit or hard_hit or hit_max_hold or ld_reason or hour_reason or flip_reason:
''',
'''                        hard_hit = impulse_hard_confirmed(symbol, trade, current_r)
                        snap_reason = snap_exit_reason(trade, current_r, hold_time)
                        if usd_loss_hit or hard_hit or hit_max_hold or ld_reason or hour_reason or flip_reason or snap_reason:
'''
),
(
'''                                    if usd_loss_hit:
                                        reason = "LOSS_$0.25"
''',
'''                                    if snap_reason:
                                        reason = snap_reason
                                    elif usd_loss_hit:
                                        reason = "LOSS_$0.25"
'''
),
(
'''def impulse_scan_row(row: dict, now: float) -> None:
''',
'''def snap_open_count() -> int:
    n = 0
    for trades in active_trades.values():
        for tr in trades.values():
            if tr.get("snap") and tr.get("entry_price"):
                n += 1
    return n


def snap_exit_reason(trade: dict, current_r: float, hold_min: float):
    if not trade.get("snap"):
        return None
    if current_r >= float(getattr(config, "SNAP_TARGET_R", 0.70)):
        return f"SNAP_TARGET R={current_r:.2f}"
    if hold_min * 60.0 >= float(getattr(config, "SNAP_MAX_HOLD_SEC", 75.0)):
        return f"SNAP_TIME hold={hold_min * 60.0:.0f}s R={current_r:.2f}"
    return None


def snap_arm(sym: str, side: str, extreme: float, anchor: float, now: float, chg: float) -> None:
    if not getattr(config, "ENABLE_SNAP", True):
        return
    if extreme <= 0 or anchor <= 0 or side not in ("BUY", "SELL"):
        return
    if sym in _snap_watch:
        return
    _snap_watch[sym] = {
        "side": side,
        "extreme": float(extreme),
        "anchor": float(anchor),
        "ts": float(now),
        "chg": float(chg),
        "pulled": False,
    }


def snap_arm_watch(now: float) -> None:
    global _snap_busy
    if not getattr(config, "ENABLE_SNAP", True) or _snap_busy:
        return
    if snap_open_count() >= int(getattr(config, "SNAP_MAX_POSITIONS", 1)):
        return
    window = float(getattr(config, "SNAP_WINDOW_SEC", 25.0))
    pull_lo = float(getattr(config, "SNAP_PULL_MIN", 0.25))
    pull_hi = float(getattr(config, "SNAP_PULL_MAX", 0.55))
    for sym, rec in list(_snap_watch.items()):
        if now - float(rec.get("ts") or 0) > window:
            _snap_watch.pop(sym, None)
            continue
        hist = _impulse_hist.get(sym)
        if not hist:
            continue
        last = float(hist[-1][1])
        anchor = float(rec["anchor"])
        extreme = float(rec["extreme"])
        side = rec["side"]
        span = extreme - anchor
        if last <= 0 or span == 0:
            _snap_watch.pop(sym, None)
            continue
        retrace = (extreme - last) / span if side == "BUY" else (last - extreme) / (anchor - extreme)
        if pull_lo <= retrace <= pull_hi:
            rec["pulled"] = True
        if not rec.get("pulled"):
            continue
        rebroke = (side == "BUY" and last >= extreme) or (side == "SELL" and last <= extreme)
        if not rebroke:
            continue
        _snap_watch.pop(sym, None)
        _snap_busy = True
        _snap_pending.add(sym)
        asyncio.create_task(snap_enter(sym, side, last, float(rec.get("chg") or 0)))
        return


async def snap_enter(symbol: str, side: str, price: float, chg: float) -> None:
    global _snap_busy
    try:
        if price <= 0 or not getattr(config, "ENABLE_SNAP", True):
            return
        if bot_paused or is_lane_in_cooldown("snap"):
            return
        if snap_open_count() >= int(getattr(config, "SNAP_MAX_POSITIONS", 1)):
            return
        if any(symbol in trades for trades in active_trades.values()):
            return
        try:
            idx = await get_index_direction()
        except Exception:
            idx = {}
        direction = str((idx or {}).get("direction") or "NEUTRAL").upper()
        agree = int((idx or {}).get("agree") or 0)
        oppose = agree >= 2 and (
            (side == "BUY" and direction == "BEAR") or (side == "SELL" and direction == "BULL")
        )
        if oppose:
            logger.info(f"🚫 SNAP index {symbol} | {side} vs {direction} {agree}/3")
            return
        try:
            book = await client.futures_order_book(symbol=symbol, limit=5)
            bid = float(book["bids"][0][0])
            ask = float(book["asks"][0][0])
            rows = book["asks"] if side == "BUY" else book["bids"]
        except Exception as e:
            logger.info(f"🚫 SNAP book {symbol} | {e}")
            return
        mid = (bid + ask) / 2.0
        if mid <= 0:
            return
        spread = (ask - bid) / mid
        if spread > float(getattr(config, "SNAP_MAX_SPREAD", 0.0012)):
            logger.info(f"🚫 SNAP spread {symbol} | {spread:.3%}")
            return
        depth = 0.0
        for px_s, qty_s in (rows or [])[:5]:
            depth += float(px_s) * float(qty_s)
        if depth < float(getattr(config, "SNAP_MIN_DEPTH", 400.0)):
            logger.info(f"🚫 SNAP thin book {symbol} | ${depth:.0f}")
            return
        stop = mid * float(getattr(config, "IMPULSE_STOP_PCT", 0.008))
        _momentum_stop[symbol] = stop
        mrs = strategy_by_name("MomentumRS")
        if mrs is None:
            return
        quality = {
            "tier": "B",
            "score": 71,
            "snap": True,
            "impulse": False,
            "momentum_rs": False,
            "daily_carry": False,
            "risk_multiplier": 1.0,
        }
        logger.info(f"🎯 SNAP {side} {symbol} | rebreak {chg:+.2f}% depth=${depth:.0f} stop={stop:.6g}")
        await place_full_entry_order(
            mrs, symbol, side, mid, stop, "B", "MomentumRS",
            0.71, quality, None, None, 0.50,
        )
    except Exception as e:
        logger.error(f"Snap enter {symbol}: {e}")
    finally:
        _snap_pending.discard(symbol)
        _snap_busy = False


def impulse_scan_row(row: dict, now: float) -> None:
'''
),
(
'''_impulse_busy = False
_impulse_pending = set()
''',
'''_impulse_busy = False
_snap_watch: Dict[str, dict] = {}
_snap_pending = set()
_snap_busy = False
_impulse_pending = set()
'''
),
]


def fail(msg):
    shutil.copy2(BACKUP, TARGET)
    print(msg)
    print(f"restored from {BACKUP} — bot file was not changed")


def swap_one(text, options, label):
    for old, new in options:
        n = text.count(old)
        if n == 1:
            return text.replace(old, new, 1), True
        if n > 1:
            return text, f"{label} count={n}"
    return text, f"{label} count=0"


def main():
    if not os.path.exists(TARGET):
        print(f"STOPPED missing {TARGET}")
        return
    shutil.copy2(TARGET, BACKUP)
    text = open(TARGET, encoding="utf-8").read()
    if "def snap_enter(" in text:
        if "SNAP_RISK = 0.0010" in text and 'getattr(config, "SNAP_RISK", 0.0010)' in text:
            fail("STOPPED snap is already the small independent size")
            return
        if text.count("SNAP_RISK = 0.0025") != 1:
            fail("STOPPED snap size count=%s" % text.count("SNAP_RISK = 0.0025"))
            return
        text = text.replace("SNAP_RISK = 0.0025", "SNAP_RISK = 0.0010", 1)
        text = text.replace(
            'getattr(config, "SNAP_RISK", 0.0025)',
            'getattr(config, "SNAP_RISK", 0.0010)',
        )
        old_cap = "sized * stop_dist > equity * 0.0035:"
        # Only the snap check sits on the line after the snap target.
        snap_at = text.find('f"🚫 SNAP size')
        if snap_at < 0:
            fail("STOPPED snap size check missing")
            return
        head = text[:snap_at]
        cap_at = head.rfind(old_cap)
        if cap_at < 0 or cap_at < len(head) - 400:
            if "equity * 0.0015:" not in head[-400:]:
                fail("STOPPED could not shrink the existing snap size")
                return
        elif cap_at >= 0:
            text = head[:cap_at] + "sized * stop_dist > equity * 0.0015:" + head[cap_at + len(old_cap):] + text[snap_at:]
        open(TARGET, "w", encoding="utf-8").write(text)
        try:
            py_compile.compile(TARGET, doraise=True)
        except Exception as e:
            fail(f"STOPPED compile: {e}")
            return
        print("DONE size-only pieces=3")
        print(f"backup={BACKUP}")
        return
    for i, (old, new) in enumerate(PAIRS, 1):
        n = text.count(old)
        if n != 1:
            fail(f"STOPPED piece {i} count={n}")
            return
        text = text.replace(old, new, 1)
    text, err = swap_one(text, [
        (
            '''    volx = traded / expected
    _impulse_next[sym] = now + 90.0
    side = "BUY" if chg > 0 else "SELL"
    global _impulse_busy
''',
            '''    volx = traded / expected
    _impulse_next[sym] = now + 90.0
    side = "BUY" if chg > 0 else "SELL"
    snap_arm(sym, side, px, float(prev[1]), now, chg)
    global _impulse_busy
'''
        ),
        (
            '''    volx = traded / expected
    _impulse_next[sym] = now + 90.0
    side = "BUY" if chg > 0 else "SELL"
    if _impulse_busy or impulse_open_count() >= int(getattr(config, "IMPULSE_MAX_POSITIONS", 1)):
''',
            '''    volx = traded / expected
    _impulse_next[sym] = now + 90.0
    side = "BUY" if chg > 0 else "SELL"
    snap_arm(sym, side, px, float(prev[1]), now, chg)
    if _impulse_busy or impulse_open_count() >= int(getattr(config, "IMPULSE_MAX_POSITIONS", 1)):
'''
        ),
    ], "snap-arm")
    if err is not True:
        fail(f"STOPPED {err}")
        return
    text, err = swap_one(text, [
        (
            '''                        impulse_arm_confirm(now)
                        impulse_arm_hold(now)
                        touch_activity()
''',
            '''                        impulse_arm_confirm(now)
                        impulse_arm_hold(now)
                        snap_arm_watch(now)
                        touch_activity()
'''
        ),
        (
            '''                        impulse_arm_confirm(now)
                        touch_activity()
''',
            '''                        impulse_arm_confirm(now)
                        snap_arm_watch(now)
                        touch_activity()
'''
        ),
    ], "snap-watch")
    if err is not True:
        fail(f"STOPPED {err}")
        return
    text, err = swap_one(text, [
        (
            '''            if getattr(config, "ENABLE_SAME_DIRECTION_CAP", True):
                same_n = count_open_side(side)
''',
            '''            if getattr(config, "ENABLE_SAME_DIRECTION_CAP", True) and not (quality_report or {}).get("snap"):
                same_n = count_open_side(side)
'''
        ),
        (
            '''            if getattr(config, "ENABLE_SAME_DIRECTION_CAP", True) and not (quality_report or {}).get("daily_carry"):
                same_n = count_open_side(side)
''',
            '''            if getattr(config, "ENABLE_SAME_DIRECTION_CAP", True) and not (quality_report or {}).get("daily_carry") and not (quality_report or {}).get("snap"):
                same_n = count_open_side(side)
'''
        ),
    ], "same-side")
    if err is not True:
        fail(f"STOPPED {err}")
        return
    text, err = swap_one(text, [
        (
            '''\n            await place_tp_ladder(symbol, side, entry_price, stop_dist, qty, strength)\n''',
            '''\n            if not (quality_report or {}).get("snap"):\n                await place_tp_ladder(symbol, side, entry_price, stop_dist, qty, strength)\n'''
        ),
        (
            '''\n            if not (quality_report or {}).get("daily_carry"):\n                await place_tp_ladder(symbol, side, entry_price, stop_dist, qty, strength)\n''',
            '''\n            if not (quality_report or {}).get("daily_carry") and not (quality_report or {}).get("snap"):\n                await place_tp_ladder(symbol, side, entry_price, stop_dist, qty, strength)\n'''
        ),
    ], "ladder")
    if err is not True:
        fail(f"STOPPED {err}")
        return
    open(TARGET, "w", encoding="utf-8").write(text)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        fail(f"STOPPED compile: {e}")
        return
    print(f"DONE pieces={len(PAIRS) + 2}")
    print(f"backup={BACKUP}")


if __name__ == "__main__":
    main()
