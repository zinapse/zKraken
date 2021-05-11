import time
import keyboard
import krakenex
from decimal import *
import configparser

if __name__ == '__main__':
    # Start time to print
    starttime = int(time.time())

    # Make sure we don't keep lowering the sell_at price too much
    lowered = 0

    # Define our configparser
    config = configparser.ConfigParser()
    config.read('z-coin.ini')

    # Config variables
    c_time = config['TIME']
    c_volume = config['VOLUME']
    c_price = config['PRICE']
    c_type = config['TYPE']
    c_api = config['API']

    # Seconds to delay each iteration
    delay = int(c_time['delay'])

    # Sell every X minutes
    delay_sell = (60 / delay) * int(c_time['attempt_minutes'])

    # API variables
    api_key = c_api['key']
    api_sec = c_api['sec']

    # Kraken API variables
    k = krakenex.API(key=api_key, secret=api_sec)

    # Trade variables
    buy_at = Decimal(0.67)
    sell_at = Decimal(0.75)
    max_buy = Decimal(c_price['max_buy'])
    coin = c_type['coin']
    currency = c_type['currency']

    # Dictionaries to send
    pair = '{coin}{currency}'.format(coin=coin, currency=currency)
    buy_dict = {
        'pair': pair,
        'ordertype': 'market', 
        'type': 'buy',
        'volume': int(c_volume['buy'])
    }
    sell_dict = {
        'pair': pair,
        'ordertype': 'market', 
        'type': 'sell',
        'volume': int(c_volume['sell'])
    }

    # Pause output
    pause = False

    # Update the config variables
    def update_config():
        # Access our configparser
        config.read('z-coin.ini')

        # Config variables
        global c_time, c_volume, c_price, c_type
        c_time = config['TIME']
        c_volume = config['VOLUME']
        c_price = config['PRICE']
        c_type = config['TYPE']

        # Seconds to delay each iteration
        global delay
        delay = int(c_time['delay'])

        # Sell every 5 minutes
        global delay_sell
        delay_sell = (60 / delay) * 5

        # Update max_buy
        global max_buy
        max_buy = Decimal(c_price['max_buy'])
        
        # Update coin and currency data
        global coin, currency
        coin = c_type['coin']
        currency = c_type['currency']

    # Update the dictionary variables
    def update_dictionaries():
        # Dictionaries to send
        global buy_dict, sell_dict
        pair = '{coin}{currency}'.format(coin=coin, currency=currency)
        buy_dict = {
            'pair': pair,
            'ordertype': 'market', 
            'type': 'buy',
            'volume': int(c_volume['buy'])
        }
        sell_dict = {
            'pair': pair,
            'ordertype': 'market', 
            'type': 'sell',
            'volume': int(c_volume['sell'])
        }

    # Get the account balance
    def get_account_balance():
        balance = k.query_private('Balance')
        try:
            balance = balance['result']
        except KeyError:
            print('[ERROR]: No balance result...')
            return False

        try:
            ret = balance['Z{}'.format(currency)]
        except KeyError:
            print('[ERROR]: No balance "Z{}"'.format('currency'))
            return False

        # Show currency
        formatted = Decimal(ret)
        print('[INFO]: Account Balance [{currency}]: {formatted:.2f}'.format(currency=currency, formatted=formatted))

        return balance

    # Get the price of a given ticker
    def get_ticker_price(ticker):
        ticker = '{ticker}{currency}'.format(ticker=ticker, currency=currency)

        dic = {'pair': ticker}
        _q = k.query_public('Ticker', data=dic)

        if(len(_q['error']) > 0):
            print('[ERROR]: ' + str(_q['error'][0]))
            return False
        
        try:
            price = _q['result'][ticker]['a'][0]
        except KeyError:
            print('[ERROR]: No ticker value')
            e = open('coin_err.txt', 'a')
            e.write('GET_TICKER_PRICE Error')
            e.write('\n')
            e.close()
            return False
        
        formatted = Decimal(price)
        print('[INFO]: Current market price [' + ticker + ']: ' + '{:.6f}'.format(formatted))
        return price
    
    # Check the market price
    current_price = get_ticker_price(coin)
    if(current_price == False):
        print('[EXIT]: Error on get_ticker_price(\'{}\')'.format(coin))
        exit()

    # Sell
    def sell():
        global max_buy

        resp = k.query_private('AddOrder', sell_dict)

        if(len(resp['error']) > 0):
            error = str(resp['error'][0])
            error = error.split(':')

            # If we don't have funds we don't need to exit, just print
            if(error[1] == 'Insufficient funds'):
                print('[!Sold]: Insufficient funds')
                max_buy = buy_at + Decimal(0.01)
                if(max_buy >= (sell_at - Decimal(0.02))):
                    max_buy = buy_at
                    config.set('PRICE', 'max_buy', '{:.3f}'.format(max_buy))
                    with open('z-coin.ini', 'w') as configfile:
                        config.write(configfile)

                return True

            print('[ERROR]: ' + str(resp['error'][0]))
            e = open('coin_err.txt', 'a')
            e.write('SELL ERROR: {}\n'.format(str(resp['error'][0])))
            e.close()
            return False
        
        # Increase the max_buy price
        max_buy = max_buy + Decimal(0.005)

        config.set('PRICE', 'max_buy', '{:.3f}'.format(max_buy))
        with open('z-coin.ini', 'w') as configfile:
            config.write(configfile)

        result = str(resp['result']['descr']['order'])
        print('[Sold]: {}: {:.6f}'.format(result, current_price))

        f = open('coin_output.txt', 'a')
        f.write('SELL ORDER: {}: {}\n'.format(result, str(current_price)))

        try:
            tx_id = str(resp['result']['descr']['txid'])
            f.write('TXID: {}\n'.format(tx_id))
        except KeyError:
            print('[INFO]: No "txid"')
        f.close()

        return True

    # Buy
    def buy():
        global sell_at
        resp = k.query_private('AddOrder', buy_dict)

        if(len(resp['error']) > 0):
            error = str(resp['error'][0])
            error = error.split(':')

            # If we don't have funds we don't need to exit, just print
            # Also decrease the sell_at price up to 5 cents
            if(error[1] == 'Insufficient funds'):
                global sell_at
                global lowered
                print('[!Bought]: Insufficient funds')
                if(lowered < 5):
                    sell_at = sell_at - Decimal(0.01)
                    config.set('PRICE', 'sell_at', '{:.3f}'.format(sell_at))
                    with open('z-coin.ini', 'w') as configfile:
                        config.write(configfile)
                    lowered += 1
                return True

            print('[ERROR]: ' + str(resp['error'][0]))
            e = open('coin_err.txt', 'a')
            e.write('BUY ERROR: {}\n'.format(str(resp['error'][0])))
            e.close()
            return False

        result = str(resp['result']['descr']['order'])
        print('[Bought]: {}: {:.6f}'.format(result, current_price))

        f = open('coin_output.txt', 'a')
        f.write('BUY ORDER: {} ({})\n'.format(result, str(current_price)))

        try:
            tx_id = str(resp['result']['descr']['txid'])
            f.write('TXID: {}\n'.format(tx_id))
        except KeyError:
            print('[INFO]: No "txid"')
        f.close()

        return True

    # Update the sell_at and buy_at prices
    def update_targets(current):
        global sell_at
        global buy_at
        sell_at = Decimal(current) + Decimal(c_price['sell'])
        buy_at = Decimal(current) - Decimal(c_price['buy'])

        if(buy_at < max_buy):
            buy_at = max_buy
    
    # Update initial buy and sell prices
    buy_at = 0
    sell_at = 0
    update_targets(current_price)
    if(buy_at < max_buy):
        buy_at = max_buy
    
    def show_menu(self):
        global pause
        if(pause == True): return

        # Pause output
        pause = True

        # Enter a command
        cmd = input('Command>')
        cmd = str(cmd).strip()

        # Check what was entered
        if(cmd == 'balance'):
            # Check account balance
            balance = get_account_balance()
            if(balance == False):
                print('[EXIT]: Error on get_account_balance()')
                exit()
            print()
        elif(cmd == 'sell at'):
            # Set the sell_at price
            tmp_sell = float(input('Price>'))
            config.set('PRICE', 'sell', '{:.3f}'.format(tmp_sell))
            print('[NOTICE]: sell_at updated to {:.3f}'.format(tmp_sell))
        elif(cmd == 'buy at'):
            # Set the buy_at price
            tmp_buy = float(input('Price>'))
            config.set('PRICE', 'buy', '{:.3f}'.format(tmp_buy))
            print('[NOTICE]: buy_at updated to {:.3f}'.format(tmp_buy))
        elif(cmd == 'sell volume'):
            # Set the sell volume to send
            sell_vol = int(input('Volume>'))
            config.set('VOLUME', 'sell', '{:.3f}'.format(sell_vol))
            print('[NOTICE]: Sell volume updated to {:.3f}'.format(sell_vol))
        elif(cmd == 'buy volume'):
            # Set the buy volume to send
            buy_vol = int(input('Volume>'))
            config.set('VOLUME', 'buy', '{:.3f}'.format(buy_vol))
            print('[NOTICE]: Sell volume updated to {:.3f}'.format(buy_vol))
        elif(cmd == 'max buy'):
            # Set the max buy price
            tmp_mb = float(input('Price>'))
            config.set('PRICE', 'max_buy', '{:.3f}'.format(tmp_mb))
            print('[NOTICE]: Max buy price set to {:.3f}'.format(tmp_mb))
        elif(cmd == 'set delay'):
            # Set a new delay
            tmp_delay = input('Seconds>')
            config.set('TIME', 'delay', tmp_delay)
            update_dictionaries()
            print('[NOTICE]: Delay updated to {}'.format(tmp_delay))
        elif(cmd == 'exit'):
            # Quitting
            print('[EXIT]: Quitting...')
            exit()
        else:
            print('[NOTICE]: Unknown command ({})'.format(str(cmd)))
            print('[INFO]: Commands: "balance", "sell at", "buy at", "sell volume", "buy volume", "max buy", "set delay"')

        # Write the new structure to the new file
        with open('z-coin.ini', 'w') as configfile:
            config.write(configfile)
        update_config()
        update_dictionaries()
        
        pause = False

    # Set our counters
    counter = delay_sell
    limit_counter = int(counter / 6)

    # Define hasDone
    hasDone = False

    # Keyboard hook
    keyboard.on_press_key('space', show_menu)

    # "Welcome" message
    print('[{}]: Starting...)'.format(str(starttime)))
    print('Press [SPACE] to enter commands.')

    while True:
        if(pause):
            time.sleep(delay)
            continue

        # Update the config and dictionary variables
        update_config()
        update_dictionaries()

        # Start this set to False
        force = False
        
        # Print sell and buy prices
        print('[INFO]: sell_at {:.3f}'.format(sell_at))
        print('[INFO]: buy_at {:.3f}'.format(buy_at))
        
        # Format the current price
        current_price = Decimal(current_price)

        # Check if we should force buy/sell
        if((current_price <= buy_at or current_price >= sell_at) and current_price > max_buy and counter != delay_sell):
            force = True

        # If it's been X (attempt_minutes) minutes, or forced
        if(counter >= delay_sell or force == True):
            # If the counter is higher than the limit we can reset hasDone
            if(counter >= limit_counter):
                hasDone = False

            if(force == False):
                # If it wasn't forced we can reset these
                hasDone = False
                counter = 0
            else:
                # If it was forced we add one to the counter and check if hasDone would be False
                counter = counter + 1

                if(counter >= delay_sell):
                    counter = 0
                    hasDone = False

                if(counter >= limit_counter):
                    hasDone = False

                # If we're still on the delay then continue after delay
                if(hasDone == True):
                    print('[No Action] (hasDone)')
                    time.sleep(delay)
                    continue
            
            # Check account balance
            balance = get_account_balance()
            if(balance == False):
                print('[EXIT]: Error on get_account_balance()')
                break
            balance = balance['Z{}'.format(currency)]

            # Wait if under max_buy and update the targets
            if(current_price < max_buy):
                print('[NOTICE]: Current market price is under max_buy ({})'.format(str(Decimal(max_buy))))
                print('[No Action]')
                update_targets(max_buy)

            # Sell if the price is more than the sell_at price
            elif(current_price >= sell_at):
                if(sell() == False):
                    print('[EXIT]: Error on sell()')
                    break
                if(force == True):
                    hasDone = True
                    limit_counter = counter + int(counter / 6)
                    if(limit_counter > delay_sell):
                        limit_counter = limit_counter - delay_sell

                update_targets(current_price)

            # Buy if the price is more than the buy_at price
            elif(current_price <= buy_at):
                if(Decimal(balance) < 20):
                    print('[INFO]: Balance less than 20, not buying')
                    print('[No Action]')
                    update_targets(current_price)
                    time.sleep(delay)
                    print('')
                    continue

                if(buy() == False):
                    print('[EXIT]: Error on buy()')
                    break
                if(force == True):
                    hasDone = True
                    limit_counter = counter + int(counter / 6)
                    if(limit_counter > delay_sell):
                        limit_counter = limit_counter - delay_sell

                update_targets(current_price)
            
            else:
                print('[No Action]')
        else:
            counter = counter + 1

        # Sleep
        time.sleep(delay)
        print('')