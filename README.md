# zKraken
 Python script to automate coin trading on Kraken. 
 
 I'm currently just working on this as a hobby project, but I hope it can be useful to someone.
 
## Issues
 ...

## Installation & Usage
 1. Download and install [Python](https://www.python.org/downloads/).
 2. Use [PIP](https://pip.pypa.io/en/stable/installation/#get-pip-py) to install `krakenex` and `datetime`. Open a command prompt/terminal:
```
pip install krakenex datetime
```
*Windows users might need to open command prompt as admin.*

 3. Download the code in this repository either with GitHub Desktop, cloning via terminal, or by clicking the Code button at the top of this page and downloading the zip file.
 4. Navigate to the folder where zKraken is, and run with the `python` command:
```
cd "DIRECTORY PATH"
python zKraken.py
```
*Linux users might need to use `python3` instead of `python`.*
 
 To close the program just press Ctrl+C.

## Configuration
 The INI file has various options you can change.
 
 > `[TIME] delay` - How many seconds to wait each iteration.
 > 
 > `[API] key` - Your Kraken API key.
 > 
 > `[API] sec` - Your Kraken API sec.
 > 

### Kraken API variables
 Create an API key and sec in your [account's API settings](https://www.kraken.com/u/security/api). You'll only see the secret (sec) once, so make sure you copy it when you make the API key. It will show a message at the top of the page when you create a key with the secret.
