from futu import *
import os

# Reference: https://openapi.futunn.com/futu-api-doc/quick/strategy-sample.html

############################ CONFIG ############################
FUTUOPEND_ADDRESS = '127.0.0.1'
FUTUOPEND_PORT = 11111

TRADING_ENVIRONMENT = TrdEnv.REAL # TrdEnv.SIMULATE
TRADING_MARKET = TrdMarket.HK
TRADING_PWD = os.getenv('FUTU_TRADING_PSWD')
if TRADING_PWD == None:
    print('No FUTU_TRADING_PSWD set in ENV')
EXAMPLE_CODE = 'HK.00700'

quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT, security_firm=SecurityFirm.FUTUSECURITIES)

def unlock_trade():
    if TRADING_ENVIRONMENT == TrdEnv.REAL:
        ret, data = trade_context.unlock_trade(TRADING_PWD)
        if ret != RET_OK:
            print('failed in unlock_trade()', data)
            return False
    return True

def get_holding_position(code):
    holding_position = 0
    ret, data = trade_context.position_list_query(code=code, trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        print('Failed in getting position', code, data)
        return None
    else:
        if data.shape[0] > 0:
            holding_position = data['qty'][0]
        print('Position {} {}'.format(code, holding_position))
    return holding_position

def get_ask_and_bid(code):
    ret, data = quote_context.get_order_book(code, num=1)
    if ret != RET_OK:
        print('No L1 for ', code, data)
        return None, None
    return data['Ask'][0][0], data['Bid'][0][0]

def price_step(code):
    open_quantity = 0
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        print('Failed in getting market snapshot', data)
    # print('Trading rule', code, data)
    # for key in data:
    #    print("\t", key, data[key])
    # lot_size -> price_step
    ret = data['lot_size'][0]
    print("\t price_step", code, ret)
    return ret

def test_buy_trade(code):
    ask, bid = get_ask_and_bid(code)
    open_quantity = 100
    if is_valid_quantity(code, open_quantity, ask) == False:
        print('Order quantity beyond valid amount.')
        return None
    ret, data = trade_context.place_order(
            price=ask, qty=open_quantity, code=code, trd_side=TrdSide.BUY,
            order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT,
            remark='moving_average_strategy')
    if ret != RET_OK:
        print('Failed in placing order', data)

############################ Callbacks ############################
def on_init():
    if not unlock_trade():
        return False
    print('************ ON_INIT ***********')
    return True

if __name__ == '__main__':
    if not on_init():
        print('Failed in on_init()')
        quote_context.close()
        trade_context.close()
    print('Do something here')
    price_step(EXAMPLE_CODE)
