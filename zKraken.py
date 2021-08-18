import time, krakenex, configparser, os
from decimal import *
from datetime import datetime

global sell_save, buy_save, last_sold, last_bought, sell_at, buy_at, current_price, \
    max_buy, exit_saves, buy_step, sell_step, buy_dict, sell_dict, min_save_time_s, max_save_time_s, min_save_time_b, max_save_time_b
sell_save = 0
buy_save = 0
max_buy = 0
min_save_time_s = 0
max_save_time_s = 0
min_save_time_b = 0
max_save_time_b = 0
exit_saves = {
    'balance': 0,
    'ticker': 0,
    'sell': 0,
    'buy': 0
}
last_sold = None
last_bought = None
buy_step = None
sell_step = None

if __name__ == '__main__':
    if(os.name == 'nt'):
        os.system('cls')
    else:
        os.system('clear')

    try:
        # Start time to print
        start_time = int(time.time())

        # Define our configparser
        config = configparser.ConfigParser()
        config.read('z-coin.ini')

        # Config variables
        c_time = config['TIME']
        c_price = config['PRICE']
        c_type = config['TYPE']
        c_api = config['API']
        c_volume = config['VOLUME']

        # Seconds to delay each iteration
        delay = int(c_time['delay'])

        # Min and max seconds before increase or decrease in sell or buy save
        min_save_time_s = int(c_time['min_save_time_sell'])
        max_save_time_s = int(c_time['max_save_time_sell'])
        min_save_time_b = int(c_time['min_save_time_buy'])
        max_save_time_b = int(c_time['max_save_time_buy'])

        # API variables
        api_key = c_api['key']
        api_sec = c_api['sec']

        # Kraken API variables
        k = krakenex.API(key=api_key, secret=api_sec)

        # Trade variables
        max_buy = Decimal(c_price['max_buy'])
        buy_step = Decimal(c_price['buy'])
        sell_step = Decimal(c_price['sell'])
        buy_volume = Decimal(c_volume['buy'])
        sell_volume = Decimal(c_volume['sell'])
        coin = c_type['coin']
        currency = c_type['currency']

        # Dictionary to send
        try:
            pair = c_type['pairstr']
        except KeyError:
            pair = '{coin}{currency}'.format(coin=coin, currency=currency)

        buy_dict = {
            'pair': pair,
            'ordertype': 'market', 
            'type': 'buy',
            'volume': buy_volume
        }
        sell_dict = {
            'pair': pair,
            'ordertype': 'market', 
            'type': 'sell',
            'volume': sell_volume
        }

        # Get the account balance
        def get_account_balance():
            """Get the current account balance.

            Returns:
                bool|Decimal: False if the function fails, or the account balance if it's successful.
            """

            global exit_saves
            try:
                balance = k.query_private('Balance')
                balance = balance['result']
            except KeyError:
                print('[ERROR]: No balance result...')
                return False
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                if(exit_saves['balance'] > 3):
                    print('[EXIT]: Max attempts made in get_account_balance()')
                    e.write('[{}] Max attempts: get_account_balance()'.format(tmp_date))
                    e.write('\n')
                    e.close()
                    exit()

                print('[ERROR]: ConnectionError get_account_balance()')
                e.write('[{}] ConnectionError: get_account_balance()'.format(tmp_date))
                e.write('\n')
                e.close()
                exit_saves['balance'] += 1
                return False
            
            exit_saves['balance'] = 0

            try:
                # Money Balance
                ret = balance['Z{}'.format(currency)]

                # Do this to format BTC
                c = coin
                if(coin == 'XBT'): c = 'XXBT'

                # Coin Balance
                ret2 = balance[c]
            except KeyError:
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                e = open('coin_err.txt', 'a')
                e.write('[{}] KeyError: get_account_balance()'.format(tmp_date))
                e.write('\n')
                e.close()

                print('[ERROR]: No balance "Z{}"'.format(currency))
                exit()

            # Show currency
            formatted = Decimal(ret)
            formatted2 = Decimal(ret2)
            print('[INFO]: Account Balance [{currency}]: {formatted:.2f}'.format(currency=currency, formatted=formatted))
            print('[INFO]: Account Balance [{currency}]: {formatted:.8f}'.format(currency=coin, formatted=formatted2))

            return balance

        # Get the price of a given ticker
        def get_ticker_price(ticker, first = False):
            """Get the price of a coin.

            Args:
                ticker (str): The coin's ticker.
                first (bool, optional): If the function is being called for the first time. Defaults to False.

            Returns:
                bool|Decimal: False if the function fails, or the coin price if it's successful.
            """

            global exit_saves

            # Format ticker variable and create a dictionary
            ticker = '{ticker}{currency}'.format(ticker=ticker, currency=currency)
            dic = {'pair': ticker}

            try:
                _q = k.query_public('Ticker', data=dic)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                if(exit_saves['ticker'] > 3):
                    print('[EXIT]: Max attempts made in get_ticker_price()')
                    e.write('[{}] Max attempts: get_ticker_price()'.format(tmp_date))
                    e.write('\n')
                    e.close()
                    exit()

                print('[ERROR]: ConnectionError get_ticker_price')
                e.write('[{}] ConnectionError: get_ticker_price()'.format(tmp_date))
                e.write('\n')
                e.close()
                exit_saves['ticker'] += 1
                return False

            if(len(_q['error']) > 0):
                print('[ERROR]: ' + str(_q['error'][0]))
                return False

            exit_saves['ticker'] = 0

            try:
                pairstr = c_type['pairstr']
            except KeyError:
                pairstr = ticker
            
            try:
                price = _q['result'][pairstr]['a'][0]
            except KeyError:
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                e = open('coin_err.txt', 'a')
                e.write('[{}] KeyError: get_ticker_price()'.format(tmp_date))
                e.write('\n')
                e.close()
                print('[ERROR]: No ticker value')
                exit()
            
            formatted = Decimal(price)
            
            # Doing this to not print twice on program start
            if(first == False): print('[INFO]: Current market price [' + ticker + ']: ' + '{:.2f}'.format(formatted))

            return price

        # "Welcome" message
        start_date = datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
        e = open('coin_err.txt', 'a')
        e.write('[{}] Starting ---------------------------------'.format(start_date))
        e.write('\n')
        e.close()
        print('[{}]: Starting...'.format(str(start_date)))
        print('')
        
        # Check the market price
        current_price = get_ticker_price(coin, True)
        if(current_price == False):
            print('[EXIT]: Error on get_ticker_price(\'{}\')'.format(coin))
            exit()

        # Sell
        def sell(price):
            """Function to sell coins.

            Args:
                price (Decimal): The price to sell at.

            Returns:
                bool: If the function was completed successfully.
            """
            global current_price, last_sold, sell_save, exit_saves, min_save_time_s, max_save_time_s
            current_price = Decimal(price)

            try:
                resp = k.query_private('AddOrder', sell_dict)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                if(exit_saves['sell'] > 3):
                    print('[EXIT]: Max attempts made in sell()')
                    e.write('[{}] Max attempts: sell()'.format(tmp_date))
                    e.write('\n')
                    e.close()
                    exit()

                print('[ERROR]: ConnectionError sell()')
                e.write('[{}] ConnectionError: sell()'.format(tmp_date))
                e.write('\n')
                e.close()
                exit_saves['sell'] += 1
                return False

            exit_saves['sell'] = 0

            if(len(resp['error']) > 0):
                error = str(resp['error'][0])
                error = error.split(':')

                # If we don't have funds we don't need to exit, just print
                if(error[1] == 'Insufficient funds'):
                    print('[!SELL]: Insufficient funds')
                    return True

                print('[ERROR]: ' + str(resp['error'][0]))
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                e.write('[{}] SELL ERROR: {}\n'.format(tmp_date, str(resp['error'][0])))
                e.close()
                return False

            result = str(resp['result']['descr']['order'])
            print('[SELL]: {}: {:.2f}'.format(result, current_price))

            f = open('coin_output.txt', 'a')
            tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            f.write('[{}] SELL ORDER: {}: {:.2f}\n'.format(tmp_date, result, current_price))
            f.close()

            if(last_sold != None):
                tmp_sold = datetime.now()
                time_diff = tmp_sold - last_sold
                seconds = int(time_diff.total_seconds())
                if(seconds < min_save_time_s): sell_save += 1
                if(seconds > max_save_time_s): sell_save -= 1

            last_sold = datetime.now()
            return True

        # Buy
        def buy(price):
            """Function to buy coins.

            Args:
                price (Decimal): The price to buy at.

            Returns:
                bool: If the function was completed successfully.
            """
            global current_price, last_bought, buy_save, exit_saves, min_save_time_b, max_save_time_b
            current_price = Decimal(price)
            
            try:
                resp = k.query_private('AddOrder', buy_dict)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                if(exit_saves['buy'] > 3):
                    print('[EXIT]: Max attempts made in buy()')
                    e.write('[{}] Max attempts: buy()'.format(tmp_date))
                    e.write('\n')
                    e.close()
                    exit()

                print('[ERROR]: ConnectionError buy()')
                e.write('[{}] ConnectionError: buy()'.format(tmp_date))
                e.write('\n')
                e.close()
                exit_saves['buy'] += 1
                return False
            
            exit_saves['buy'] = 0

            if(len(resp['error']) > 0):
                error = str(resp['error'][0])
                error = error.split(':')

                # If we don't have funds we don't need to exit, just print
                if(error[1] == 'Insufficient funds'):
                    print('[!BUY]: Insufficient funds')

                print('[ERROR]: ' + str(resp['error'][0]))
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                e.write('[{}] BUY ERROR: {}\n'.format(tmp_date, str(resp['error'][0])))
                e.close()
                return False

            result = str(resp['result']['descr']['order'])
            print('[BUY]: {}: {:.2f}'.format(result, current_price))

            f = open('coin_output.txt', 'a')
            tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            f.write('[{}] BUY ORDER: {}: {:.2f}\n'.format(tmp_date, result, current_price))
            f.close()

            if(last_bought != None):
                tmp_bought = datetime.now()
                time_diff = tmp_bought - last_bought
                seconds = int(time_diff.total_seconds())
                if(seconds < min_save_time_b): buy_save += 1
                if(seconds > max_save_time_b): buy_save -= 1

            last_bought = datetime.now()
            return True

        # Update the sell_at and buy_at prices
        def update_targets(current):
            """Function to update the sell_at and buy_at variables.

            Args:
                current (Decimal): The current price of the coin.
            """

            global sell_at, buy_at, sell_save, buy_save, max_buy, buy_step, sell_step
            sell_at = Decimal(current) + Decimal(sell_step)
            buy_at = Decimal(current) - Decimal(buy_step)

            if(sell_save < 1): sell_save = 1
            else: sell_at += Decimal(sell_step) * Decimal(sell_save)

            if(buy_save < 1): buy_save = 1
            else: buy_at -= Decimal(buy_step) * Decimal(buy_save)

            if(buy_at > max_buy): buy_at = max_buy
        
        # Main loop
        def main_loop():
            """The main function loop.
            """

            global sell_at, buy_at, delay, buy_step, sell_step, buy_save, sell_save, buy_volume, sell_volume, buy_dict, sell_dict, \
                min_save_time_s, max_save_time_s, min_save_time_b, max_save_time_b

            while True:
                # Format and print the current price
                current_price = get_ticker_price(coin)
                current_price = Decimal(current_price)

                # Update config
                config.read('z-coin.ini')
                c_time = config['TIME']
                c_price = config['PRICE']
                c_volume = config['VOLUME']

                # Checking for INI changes
                if(delay != int(c_time['delay'])):
                    delay = int(c_time['delay'])
                    print('[INI]: delay = {}'.format(delay))

                if(min_save_time_s != int(c_time['min_save_time_sell'])):
                    min_save_time_s = int(c_time['min_save_time_sell'])
                    print('[INI]: min_save_time_s = {}'.format(min_save_time_s))
                if(max_save_time_s != int(c_time['max_save_time_sell'])):
                    max_save_time_s = int(c_time['max_save_time_sell'])
                    print('[INI]: max_save_time_s = {}'.format(max_save_time_s))

                if(min_save_time_b != int(c_time['min_save_time_buy'])):
                    min_save_time_b = int(c_time['min_save_time_buy'])
                    print('[INI]: min_save_time_b = {}'.format(min_save_time_b))
                if(max_save_time_b != int(c_time['max_save_time_buy'])):
                    max_save_time_b = int(c_time['max_save_time_buy'])
                    print('[INI]: max_save_time_b = {}'.format(max_save_time_b))

                if(buy_step != int(c_price['buy'])):
                    buy_step = int(c_price['buy'])
                    print('[INI]: buy_step = {}'.format(buy_step))
                    buy_save = 1
                    sell_save = 1
                    update_targets(current_price)
                if(sell_step != int(c_price['sell'])):
                    sell_step = int(c_price['sell'])
                    print('[INI]: sell_step = {}'.format(sell_step))
                    buy_save = 1
                    sell_save = 1
                    update_targets(current_price)
                    
                if(buy_volume != Decimal(c_volume['buy'])):
                    buy_volume = Decimal(c_volume['buy'])
                    buy_dict = {
                        'pair': pair,
                        'ordertype': 'market', 
                        'type': 'buy',
                        'volume': buy_volume
                    }
                    print('[INI]: buy_volume = {}'.format(buy_volume))
                if(sell_volume != Decimal(c_volume['sell'])):
                    sell_volume = Decimal(c_volume['sell'])
                    sell_dict = {
                        'pair': pair,
                        'ordertype': 'market', 
                        'type': 'sell',
                        'volume': sell_volume
                    }
                    print('[INI]: sell_volume = {}'.format(sell_volume))

                # Print sell and buy prices
                print('[INFO]: sell @ {:.2f} (save = {})'.format(sell_at, sell_save))
                print('[INFO]: buy  @ {:.2f} (save = {})'.format(buy_at, buy_save))
                    
                # Check account balance
                balance = get_account_balance()
                if(balance == False):
                    print('Waiting...')
                    print('')
                    time.sleep(delay)
                    continue
                balance = balance['Z{}'.format(currency)]

                # Sell if the price is more than the sell_at price
                if(current_price >= sell_at):
                    if(sell(current_price) == False):
                        print('Waiting...')
                        print('')
                        time.sleep(delay)
                        continue

                    update_targets(current_price)

                # Buy if the price is less than the buy_at price
                elif(current_price <= buy_at and current_price <= max_buy):
                    if(Decimal(balance) < 100):
                        print('[INFO]: Balance less than 100, not buying')
                        print('[No Action]')
                        update_targets(current_price)
                        print('Waiting...')
                        print('')
                        time.sleep(delay)
                        continue

                    if(buy(current_price) == False):
                        print('Waiting...')
                        print('')
                        time.sleep(delay)
                        continue

                    update_targets(current_price)
                
                else:
                    print('[No Action]')

                # Sleep
                print('Waiting...')
                time.sleep(delay)
                print('')
        
        # Update initial buy and sell prices
        buy_at = 0
        sell_at = 0
        update_targets(current_price)
    
    except Exception as ex:
        e = open('coin_err.txt', 'a')
        e.write(str(ex))
        print('')
        print('!!!!!!!!!!!!!!!!')
        print('Exception thrown')
        print(str(ex))
        print('')

        e.write('\n')
        e.close()
        exit()
    
    # "start" here
    while(True):
        try:
            # Start the loop
            main_loop()

        except KeyboardInterrupt:
            print('')
            print('Exiting...')
            exit()
        
        except Exception as ex:
            e = open('coin_err.txt', 'a')
            e.write(str(ex))
            print('')
            print('!!!!!!!!!!!!!!!!')
            print('Exception thrown')
            print(str(ex))
            print('')

            e.write('\n')
            e.close()

            time.sleep(delay)
            continue
