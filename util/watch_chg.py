from futu import *
import os, math, time
from datetime import datetime

FUTUOPEND_ADDR = os.getenv('FUTU_TRADING_ADDR') or '127.0.0.1'
FUTUOPEND_PORT = os.getenv('FUTU_TRADING_PORT') or 11111

def create_default_trade_context():
    return OpenSecTradeContext(
            filter_trdmarket=TrdMarket.HK,
            host=FUTUOPEND_ADDR,
            port=FUTUOPEND_PORT,
            security_firm=SecurityFirm.FUTUSECURITIES
            )

def _print_data_table(data):
    print(data)
    for key in data:
        col = data[key].values.tolist()
        if col == ['N/A'] or col == [0.0] or data[key].isnull().values.all():
            continue
        print("\t", key, col)

class TradeOrderEventPrinter(TradeOrderHandlerBase):
     def on_recv_rsp(self, rsp_pb): # order update push
         ret, content = super(TradeOrderEventPrinter, self).on_recv_rsp(rsp_pb)
         if ret == RET_OK:
             print("<-- TradeOrderEventPrinter")
             _print_data_table(content)
         return ret, content

class TradeDealEventPrinter(TradeDealHandlerBase):
     def on_recv_rsp(self, rsp_pb): # order match update push
         ret, content = super(TradeDealEventPrinter, self).on_recv_rsp(rsp_pb)
         if ret == RET_OK:
             print("<-- TradeDealEventPrinter")
             _print_data_table(content)
         return ret, content

def watch_chg(trade_context_list=None, on_chg_cb=None):
    # Init trade_context_list as HK market only.
    if trade_context_list is None:
        trade_context_list = [create_default_trade_context()]
    account_info_cache = []
    position_cache = []
    for ctx in trade_context_list:
        ctx.set_handler(TradeOrderEventPrinter()) # Recv order events.
        account_info_cache.append(None)
        position_cache.append(None)

    wait_char_list = '\|/-'
    wait_ct = 0
    while True:
        wait_ct += 1
        print("\r", wait_char_list[wait_ct % 4], end='')
        time.sleep(1)
        idx = -1
        for trade_context in trade_context_list:
            idx += 1
            changed = False
            # Query and show diff for account
            ret, data = trade_context.accinfo_query()
            if ret != RET_OK:
                print('<-- accinfo_query error: ', idx, datetime.now(), data)
                continue
            if account_info_cache[idx] is None:
                changed = True
                print(datetime.now(), "Account info", idx)
                _print_data_table(data)
                account_info_cache[idx] = data
            diff = account_info_cache[idx].compare(data)
            if diff.empty is False:
                changed = True
                print('<-- accinfo diff', datetime.now(), idx)
                print(diff)
                account_info_cache[idx] = data

            # Query and show diff for position
            ret, data = trade_context.position_list_query()
            if ret != RET_OK:
                print('<-- position_list_query error: ', idx, datetime.now(), data)
                continue
            if position_cache[idx] is None:
                changed = True
                print(datetime.now(), "Position info", idx)
                _print_data_table(data)
                position_cache[idx] = data
            diff = position_cache[idx].compare(data)
            if diff.empty is False:
                changed = True
                print('<-- position diff', datetime.now(), idx)
                print(diff)
                position_cache[idx] = data

            if on_chg_cb != None and changed:
                on_chg_cb(account_info=account_info_cache[idx], position=position_cache[idx])

if __name__ == '__main__':
    watch_chg()
