import time, krakenex, configparser, os
from decimal import *
from datetime import datetime

if __name__ == '__main__':
    os.system('clear')

    try:
        # Make sure we don't sell or buy too much
        global sell_save, buy_save, last_sold, last_bought, sell_at, buy_at
        sell_save = 0
        buy_save = 0
        last_sold = None
        last_bought = None

        # Start time to print
        starttime = int(time.time())

        # Define our configparser
        config = configparser.ConfigParser()
        config.read('z-coin.ini')

        # Config variables
        c_time = config['TIME']
        c_price = config['PRICE']
        c_type = config['TYPE']
        c_api = config['API']

        # Minutes to delay each iteration
        delay = int(c_time['delay']) * 60

        # API variables
        api_key = c_api['key']
        api_sec = c_api['sec']

        # Kraken API variables
        k = krakenex.API(key=api_key, secret=api_sec)

        # Trade variables
        max_buy = Decimal(c_price['max_buy'])
        coin = c_type['coin']
        currency = c_type['currency']

        # Dictionaries to send
        try:
            pair = c_type['pairstr']
        except KeyError:
            pair = '{coin}{currency}'.format(coin=coin, currency=currency)

        buy_dict = {
            'pair': pair,
            'ordertype': 'market', 
            'type': 'buy',
            'volume': Decimal(0.003)
        }
        sell_dict = {
            'pair': pair,
            'ordertype': 'market', 
            'type': 'sell',
            'volume': Decimal(0.002)
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
                ret2 = balance['XXBT']
            except KeyError:
                print('[ERROR]: No balance "Z{}"'.format('currency'))
                return False

            # Show currency
            formatted = Decimal(ret)
            formatted2 = Decimal(ret2)
            print('[INFO]: Account Balance [{currency}]: {formatted:.2f}'.format(currency=currency, formatted=formatted))
            print('[INFO]: Account Balance [XXBT]: {formatted:.8f}'.format(formatted=formatted2))

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
                pairstr = c_type['pairstr']
            except KeyError:
                pairstr = ticker
            
            try:
                price = _q['result'][pairstr]['a'][0]
            except KeyError:
                print('[ERROR]: No ticker value')
                e = open('coin_err.txt', 'a')
                e.write('GET_TICKER_PRICE Error')
                e.write('\n')
                e.close()
                return False
            
            formatted = Decimal(price)
            print('[INFO]: Current market price [' + ticker + ']: ' + '{:.2f}'.format(formatted))
            return price

        # "Welcome" message
        print('[{}]: Starting...)'.format(str(starttime)))
        print('')
        
        # Check the market price
        global current_price
        current_price = get_ticker_price(coin)
        if(current_price == False):
            print('[EXIT]: Error on get_ticker_price(\'{}\')'.format(coin))
            exit()

        # Sell
        def sell():
            global current_price, last_sold, sell_save

            resp = k.query_private('AddOrder', sell_dict)

            if(len(resp['error']) > 0):
                error = str(resp['error'][0])
                error = error.split(':')

                # If we don't have funds we don't need to exit, just print
                if(error[1] == 'Insufficient funds'):
                    print('[!Sold]: Insufficient funds')
                    return True

                print('[ERROR]: ' + str(resp['error'][0]))
                e = open('coin_err.txt', 'a')
                e.write('SELL ERROR: {}\n'.format(str(resp['error'][0])))
                e.close()
                return False

            result = str(resp['result']['descr']['order'])
            print('[Sold]: {}: {:.6f}'.format(result, current_price))

            f = open('coin_output.txt', 'a')
            f.write('SELL ORDER: {}: {}\n'.format(result, str(current_price)))

            # Output and log the "txid" field if it's returned
            try:
                tx_id = str(resp['result']['descr']['txid'])
                f.write('TXID: {}\n'.format(tx_id))
            except KeyError:
                print('[INFO]: No "txid"')
            f.close()

            if(last_sold != None):
                tmp_sold = datetime.now()
                time_diff = tmp_sold - last_sold
                mins = int(time_diff.total_seconds() / 60)
                if(mins < 30): sell_save += 1
                if(mins > 120): sell_save -= 1

            last_sold = datetime.now()
            return True

        # Buy
        def buy():
            global current_price, last_bought, buy_save
            
            resp = k.query_private('AddOrder', buy_dict)

            if(len(resp['error']) > 0):
                error = str(resp['error'][0])
                error = error.split(':')

                # If we don't have funds we don't need to exit, just print
                if(error[1] == 'Insufficient funds'):
                    print('[!Bought]: Insufficient funds')

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

            if(last_bought != None):
                tmp_bought = datetime.now()
                time_diff = tmp_bought - last_bought
                mins = int(time_diff.total_seconds() / 60)
                if(mins < 30): buy_save += 1
                if(mins > 120): buy_save -= 1

            last_bought = datetime.now()
            return True

        # Update the sell_at and buy_at prices
        def update_targets(current):
            global sell_at, buy_at, sell_save, buy_save
            sell_at = Decimal(current) + Decimal(700.00)
            buy_at = Decimal(current) - Decimal(500.00)

            if(sell_save < 0): sell_save = 0
            if(sell_save > 1): sell_at += Decimal(300.00) * Decimal(sell_save)

            if(buy_save < 0): buy_save = 0
            if(buy_save > 1): buy_at -= Decimal(300.00) * Decimal(buy_save)

            if(buy_at > max_buy):
                buy_at = max_buy
        
        # Main loop
        def main_loop():
            global sell_at, buy_at

            while True:
                # Format and print the current price
                current_price = get_ticker_price(coin)
                current_price = Decimal(current_price)

                # Print sell and buy prices
                print('[INFO]: sell_at {:.2f}'.format(sell_at))
                print('[INFO]: buy_at {:.2f}'.format(buy_at))
                    
                # Check account balance
                balance = get_account_balance()
                if(balance == False):
                    print('[EXIT]: Error on get_account_balance()')
                    break
                balance = balance['Z{}'.format(currency)]

                # Sell if the price is more than the sell_at price
                if(current_price >= sell_at):
                    if(sell() == False):
                        print('[EXIT]: Error on sell()')
                        break

                    update_targets(current_price)

                # Buy if the price is less than the buy_at price
                elif(current_price <= buy_at and current_price <= max_buy):
                    if(Decimal(balance) < 100):
                        print('[INFO]: Balance less than 100, not buying')
                        print('[No Action]')
                        update_targets(current_price)
                        time.sleep(delay)
                        print('')
                        continue

                    if(buy() == False):
                        print('[EXIT]: Error on buy()')
                        break

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
    
    except ConnectionError as ex:
        e = open('coin_err.txt', 'a')
        e.write(ex.strerror)
        print('')
        print('!!!!!!!!!!!!!!!!')
        print('Exception thrown')
        print(ex.strerror)
        print('')

        e.write('\n')
        e.close()
    
    # "start" here
    while(True):
        try:
            # Start the loop
            main_loop()

        except KeyboardInterrupt:
            print('')
            print('Exiting...')
            exit()
        
        except ConnectionError as ex:
            e = open('coin_err.txt', 'a')
            e.write(ex.strerror)
            print('')
            print('!!!!!!!!!!!!!!!!')
            print('Exception thrown')
            print(ex.strerror)
            print('')

            e.write('\n')
            e.close()

            time.sleep(delay)
            pass