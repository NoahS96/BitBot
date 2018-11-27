<img src="https://media.mnn.com/assets/images/2017/01/Sloth-Hanging-Tree-Branch.jpg.638x0_q80_crop-smart.jpg" align="right" width="300" height="300"/>

# BitBot
BitBot is a command-line cryptocurrency trading bot that uses the Poloniex Python API. It is still earlier in it's 
creation but eventually I would like it to do the following:

* Allow the use of different exchange APIs
* Implement a simple GUI
* Allow the loading of different policies (and the user to make their own policies)

## Issues
* Does not currently support pure Bitcoin trading. Must use an alt coin (i.e. ETH, XRP, STR, etc.)
* Has a problem where the with buying/selling immediatly after a sell/buy and continues to repeat this. (This has been fixed by increasing the action interval/delay)

## Dependencies
* Python 3.5
* pandas (0.23.4)
* numpy (1.15.0)
* urllib3 (1.23)
* curses or windows-curses (1.0)
* websocket (0.2.1)
* websocket-client (0.51.0)

## Setup
Just clone the repository and use the Bitbot folder, add your API key and secret to bitbot.config, and then run Bitbot.py. Currently there is no GUI so it will display information in the running shell. You may want to tweak the parameters in bitbot.config first (you may want to increase the action_interval to avoid violating the API call limits).

## Policy Creation
To create a custom policy, use the policy template class in the policies folder and implement it in your own custom python class. The should_buy/should_sell functions receive the following dictionary as an argument:  

&nbsp;&nbsp;&nbsp;&nbsp;{ candle_period, measurement_period, currencyPair, printQueue, printQueueLock, removeQueue, removeQueueLock,  
&nbsp;&nbsp;&nbsp;&nbsp;candlesticks, priceCharts, sellPrice, buyPrice }.  

The third function, cleanUp, is used to reset any temporary variables your policy is keeping track of and is called after a buy or sell order. To make the bot use the policy, add it to the bitbot.config policy_file parameter.

## BitBot.py
This is the main script which grabs the configurations from bitbot.config and starts the other threads. This is
what the user will call to start the bot. Currently working on adding a way to manage the threads and kill them gracefully
if the user wishes to exit the program.

## [TraderThread.py](https://github.com/NoahS96/Bitbot/blob/master/Bitbot/lib/TraderThread.py)
This thread will handle monitoring the Poloniex prices and implementing the selected trading polocy to determine 
whether or not to buy or sell a coin. The trader thread will load the specified policy found in bitbot.config and 
use its' implemented methods to make a buy/sell decision and then execute it.

## [PrinterThread.py](https://github.com/NoahS96/Bitbot/blob/master/Bitbot/lib/PrinterThread.py)
This thread handles setting up the screen to display what the bot is doing by providing pricing updates and action aupdates.
Any thread that wants to have the printer display information can pass a key and value to the printQueue and the printer will
take care of the rest. The key is the title/description of the information and the value is the information itself. 
Currently this only works with Windows. 

## [BitBotCDO.py](https://github.com/NoahS96/Bitbot/blob/master/Bitbot/Config/bitbot.config)
This is a module which holds all of the configurations for BitBot and other threads may reference it to implement the configurations.

## [BollingerPolicy.py](https://github.com/NoahS96/Bitbot/blob/master/Bitbot/policy/BollingerPolicy.py)
This module holds the tools needed to implement the Bollinger band based trading policy. Works by calculating the Bollinger
bands for a currency's history makes its' decisions based on the following criteria:
* If the current price is n% above the lower band and the slope of the lower band is not negative, buy
* If the upper band and SMA band slopes' are greater than n, buy
* If the current price is n% less than the buy price, sell
* If the current price is n% below the highest price sine purchase. sell
* If the upper band and SMA band slopes' are less than n, sell

## [ZonePolicy.py](https://github.com/NoahS96/Bitbot/blob/master/Bitbot/policy/ZonePolicy.py)
