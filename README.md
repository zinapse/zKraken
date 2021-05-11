# zKraken
 Python script to automate coin trading on Kraken.

## Installation & Usage
 1. Download and install [Python](https://www.python.org/downloads/).
 2. Use PIP to install `keyboard` and `krakenex`. Open a command prompt as admin and type:
```
pip install keyboard krakenex
```
 3. Download the code in this repository either with GitHub Desktop, or by clicking the Code button at the top of this page and downloading the zip file.
 4. Navigate to the folder where zKraken is installed to and type:
```
cd "DIRECTORY PATH"
python zKraken.py
```

 If you press the spacebar you can enter a few different commands to change INI settings while running. If you type nothing and hit enter you'll see a list of commands. (type them without the quotation marks)
 
 To close the program just press Ctrl+C.

## Configuration
 The INI file has various options you can change.
 
 > `[TIME] delay` - How many seconds to wait each iteration.
 > 
 > `[TIME] attempt_minutes` - How many minutes it will wait to test for a buy/sell without checking prices.
 > 
 > `[VOLUME] buy` - How many coins to buy at once.
 > 
 > `[VOLUME] sell` - How many coins to sell at once.
 > 
 > `[PRICE] buy` - How much to subtract from `buy_at` each time a transaction is made.
 > 
 > `[PRICE] sell` - How much to add to `sell_at` each time a transaction is made.
 > 
 > `[TYPE] coin` - The coin ticker to use.
 > 
 > `[TYPE] currency` - The currency to use.
 > 
 > `[API] key` - Your Kraken API key.
 > 
 > `[API] sec` - Your Kraken API sec.
 > 

### Kraken API variables
 Create an API key and sec in your [account's API settings](https://www.kraken.com/u/security/api). You'll only see the secret (sec) once, so make sure you copy it when you make the API key. It will show a message at the top of the page when you create a key with the secret.
