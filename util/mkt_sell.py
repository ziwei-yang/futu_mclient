from futu import *
import os, math, time
from datetime import datetime

FUTUOPEND_ADDR = os.getenv('FUTU_TRADING_ADDR') or '127.0.0.1'
FUTUOPEND_PORT = os.getenv('FUTU_TRADING_PORT') or 11111

from watch_chg import *

quote_context = OpenQuoteContext(host=FUTUOPEND_ADDR, port=FUTUOPEND_PORT)
trade_context = create_default_trade_context()

def _print_data_table(data):
    print(data)
    for key in data:
        col = data[key].values.tolist()
        if col == ['N/A'] or col == [0.0] or data[key].isnull().values.all():
            continue
        print("\t", key, col)

def trading_rules(code_list):
    open_quantity = 0
    ret, data = quote_context.get_market_snapshot(code_list)
    if ret != RET_OK:
        print('<-- Failed in getting market snapshot', data)
    print('<-- Trading rule & market snapshot', code_list)
    # _print_data_table(data)
    qty_step_map = {}
    price_step_map = {}
    for idx, row in data.iterrows():
        code = row['code']
        qty_step = row['lot_size']
        price_step = row['price_spread']
        print("<--", code, 'qty', qty_step, 'price_step', price_step)
        qty_step_map[code] = qty_step
        price_step_map[code] = price_step
    return qty_step_map, price_step_map

def unlock_trade():
    pswd = os.getenv('FUTU_TRADING_PSWD')
    if pswd == None:
        print('No FUTU_TRADING_PSWD set in ENV')
        return False
    ret, data = trade_context.unlock_trade(pswd)
    if ret != RET_OK:
        print('<-- failed in unlock_trade()', data)
        return False
    print("<-- Trade unlocked")
    return True

def market_sell(code, qty):
    print("Will market sell", code, qty)
    input("Enter to start")
    ret, data = trade_context.place_order(
            99999, # Does not matter in MKT_ORDER
            qty, code, TrdSide.SELL,
            order_type=OrderType.MARKET,
            trd_env=TrdEnv.REAL
            )
    if ret != RET_OK:
        print('<-- failed in place_order()', data)
        return False
    print(data)
    _print_data_table(data)
    input("Enter to finish market_sell()")
    return True

def liquidate_all(code_list):
    if not unlock_trade():
        return print("Failed to unlock_trade()")
    qty_step_map, price_step_map = trading_rules(code_list)
    # Prepare lambda to sell target stocks in lots.
    def pos_changed(account_info=None, position=None):
        print('pos_changed lambda invoked.')
        for idx, row in position.iterrows():
            if row['code'] in code_list:
                lot = qty_step_map[row['code']]
                code = row['code']
                print('pos_changed', code, row['stock_name'], row['can_sell_qty'], 'lot', lot)
                sell_qty = Math.floor(row['can_sell_qty']/lot) * lot
                if sell_qty > 0:
                    market_sell(row['code'], qty)
    # util/watch_chg.py
    watch_chg(on_chg_cb=pos_changed)

if __name__ == '__main__':
    liquidate_all(['HK.09618'])
