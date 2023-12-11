import time, krakenex, configparser, os
from decimal import *
from datetime import datetime

if __name__ == '__main__':
    if(os.name == 'nt'):
        os.system('cls')
    else:
        os.system('clear')

    try:
        global delay, max_buy, buy_volume, sell_volume, buy_dict, sell_dict, fee
        
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

        # API variables
        api_key = c_api['key']
        api_sec = c_api['sec']

        # Kraken API variables
        k = krakenex.API(key=api_key, secret=api_sec)

        # Trade variables
        max_buy = Decimal(c_price['max_buy'])
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

        def round_nearest_large(x, num = 50000):
            """Round x to the closest "num".

            Args:
                x (int): The number to round.
                num (int, optional): Closest number to round to. Defaults to 50000.

            Returns:
                int: The rounded number.
            """
            return ((x + num // 2) // num) * num

        # Get the account balance
        def get_account_balance():
            """Get the current account balance.

            Returns:
                bool|Decimal: False if the function fails, or the account balance if it's successful.
            """

            try:
                balance = k.query_private('Balance')
                balance = balance['result']
            except KeyError:
                print('[ERROR]: No balance result...')
                return False
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                print('[ERROR]: ConnectionError get_account_balance()')
                e.write('[{}] ConnectionError: get_account_balance()'.format(tmp_date))
                e.write('\n')
                e.close()
                return False

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

            # Format ticker variable and create a dictionary
            ticker = '{ticker}{currency}'.format(ticker=ticker, currency=currency)
            dic = {'pair': ticker}

            try:
                _q = k.query_public('Ticker', data=dic)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                print('[ERROR]: ConnectionError get_ticker_price')
                e.write('[{}] ConnectionError: get_ticker_price()'.format(tmp_date))
                e.write('\n')
                e.close()
                return False

            if(len(_q['error']) > 0):
                print('[ERROR]: ' + str(_q['error'][0]))
                return False

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
            
            # Doing this to not print twice on program start
            if(first == False): print('[INFO]: Current market price [' + ticker + ']: ' + '{:.2f}'.format(Decimal(price)))

            return price

        # Get the current fee
        def get_fee(ticker):
            """Get the current fee for trading.

            Args:
                ticker (str): The coin's ticker.

            Returns:
                bool|Decimal: False if the function fails, or the current fee.
            """
            
            # Format ticker variable and create a dictionary
            ticker = '{ticker}{currency}'.format(ticker=ticker, currency=currency)
            dic = {'pair': ticker}
            
            try:
                _q = k.query_public('AssetPairs', data=dic)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                print('[ERROR]: ConnectionError get_fee')
                e.write('[{}] ConnectionError: get_fee()'.format(tmp_date))
                e.write('\n')
                e.close()
                return False

            if(len(_q['error']) > 0):
                print('[ERROR]: ' + str(_q['error'][0]))
                return False

            try:
                pairstr = c_type['pairstr']
            except KeyError:
                pairstr = ticker
            
            try:
                fee = _q['result'][pairstr]['fees'][0]
            except KeyError:
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                e = open('coin_err.txt', 'a')
                e.write('[{}] KeyError: get_ticker_price()'.format(tmp_date))
                e.write('\n')
                e.close()
                print('[ERROR]: No ticker value')
                exit()
            
            return fee

        # Sell
        def sell(price):
            """Function to sell coins.

            Args:
                price (Decimal): The price to sell at.

            Returns:
                bool: If the function was completed successfully.
            """
            global current_price
            current_price = Decimal(price)

            try:
                resp = k.query_private('AddOrder', sell_dict)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                print('[ERROR]: ConnectionError sell()')
                e.write('[{}] ConnectionError: sell()'.format(tmp_date))
                e.write('\n')
                e.close()
                return False

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

            return True

        # Buy
        def buy(price):
            """Function to buy coins.

            Args:
                price (Decimal): The price to buy at.

            Returns:
                bool: If the function was completed successfully.
            """
            global current_price, buy_dict, last_buy
            current_price = Decimal(price)
            
            try:
                resp = k.query_private('AddOrder', buy_dict)
            except ConnectionError:
                e = open('coin_err.txt', 'a')
                tmp_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                print('[ERROR]: ConnectionError buy()')
                e.write('[{}] ConnectionError: buy()'.format(tmp_date))
                e.write('\n')
                e.close()
                return False

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

            last_buy = current_price
            return True
        
        def calculate_profit(last_buy):
            global fee
            return Decimal(last_buy * fee)
        
        # Main loop
        def main_loop():
            """The main function loop.
            """

            global delay, buy_volume, sell_volume, buy_dict, sell_dict, max_buy, last_sell, last_buy

            while True:
                # Format and print the current price
                current_price = Decimal(get_ticker_price(coin))

                # Update config
                config.read('z-coin.ini')
                c_time = config['TIME']
                c_price = config['PRICE']
                c_volume = config['VOLUME']

                # Checking for INI changes
                if(delay != int(c_time['delay'])):
                    delay = int(c_time['delay'])
                    print('[INI]: delay = {}'.format(delay))
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
                if(max_buy != Decimal(c_price['max_buy'])):
                    max_buy = Decimal(c_price['max_buy'])
                    print('[INI] max_buy = {}').format(max_buy)
                
                # Check account balance
                balance = get_account_balance()
                if(balance == False):
                    print('Waiting for balance...')
                    print('')
                    time.sleep(delay)
                    continue
                balance = balance['Z{}'.format(currency)]
                
                # Buy if we haven't already and it's under max_buy
                if(last_buy == None):
                    if(balance > 0 and current_price <= max_buy):
                        buy(current_price)
                        last_buy = current_price
                else:
                    # We have bought before, calculate profit
                    profit = calculate_profit(last_buy)
                    
                    # If we profit 50 or more then sell
                    if(profit > 50):
                        sell(current_price)
                        last_sell = current_price

                # Sleep
                time.sleep(delay)
    
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
    
    # Welcome message
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
    
    fee = get_fee(coin)
    if(fee == False):
        print('[EXIT]: Error on get_fee(\'{}\')').format(coin)
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
