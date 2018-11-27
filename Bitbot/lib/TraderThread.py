#### TraderThread ####
# This class implements a thread which monitors the prices of a cryptocurrency via Poloniex. The trader decides its' 
# trading policy from the Bitbot_CDO and makes its' buy/sell decisions from the corresponding policy class. Any 
# information printed is sent to the printer thread via the printQueue.

import threading, time, datetime
from lib.PrinterThread import PrinterThread
from lib import Bitbot_CDO
from lib.Logger import Logger

class TraderThread(threading.Thread):

    # Constants
    __BUY_PHASE__ = 0
    __SELL_PHASE__ = 1
    __ACCOUNTS_EMPTY__ = 2

    # Attributes
    __request_interval__ = 5.0      # How often the thread will call the PoloniexAPI
    __poloniexAPI__ = None
    __Logger__ = None
    __measurement_period__ = None   # The n number of units used when calculating the Bollinger bands (20-day, 50-hour, etc.)
    __candlestick_period__ = None
    __period_unit__ = None          # The unit of measurement when calculating the Bollinger bands (days, hours, minutes)
    __orders_are_pending__ = False  # Indicates if orders have not cleared yet
    __policy_class__ = None
    __subjectCurrency__ = None
    __principalCurrency__ = 'BTC'

#    __init__
#       - Parameters:   
#           * (threadID) Number identifying this thread
#           * (name) Name identifying this thread
#           * (printQueue) The shared queue among the threads used to send printable objects to the printer thread
#           * (printQueueLock) A lock on the printQueue to prevent others from using it when it is being written to
#           * (removeQueue) A queue used to remove entries from the Trader thread dictionary. Put a key that is 
#                           already present in the dictionary into the queue to remove it.
#           * (removeQueueLock) A lock on the removeQueue to prevent others from using it.
#           * (poloniexAPI) A poloniex class that already contains the API credentials
#       - Purpose:  
#           Initialize the class properties.
    def __init__(self, threadID, name, printQueue, printQueueLock, removeQueue, removeQueueLock, poloniexAPI):
       super(TraderThread, self).__init__()
       self._stop_event = threading.Event()
       self.threadID = threadID
       self.name = name
       self.printQueue = printQueue
       self.printQueueLock = printQueueLock
       self.removeQueue = removeQueue
       self.removeQueueLock = removeQueueLock
       self.__poloniexAPI__ = poloniexAPI
       self.__Logger__ = Logger()
       self.__Logger__.writeFile("########## %s ##########" % (datetime.datetime.now()))
       self.__request_interval__ = int(Bitbot_CDO.action_interval)
       self.__measurement_period__ = int(Bitbot_CDO.measurement_period)
       self.__candlestick_period__ = Bitbot_CDO.candlestick_period
       self.__period_unit__ = Bitbot_CDO.period_unit
       self.__subjectCurrency__ = Bitbot_CDO.crypto_coin

       # Load custom trading policy class
       try:
           policyModuleName = Bitbot_CDO.policy_file
           policyClassName = policyModuleName.split('.')[-1]
           policyModule = __import__(policyModuleName, fromlist=[policyClassName])
           self.__policy_class__ = getattr(policyModule, policyClassName)
       except Exception as e:
            #print("Error loading trading policy. Not such policy %s\n%s" % (Bitbot_CDO.policy_file, str(e)))
            self.printQueueLock.acquire()
            self.printQueue.put(("Error", "Error loading trading policy. Not such policy %s\n%s" % (Bitbot_CDO.policy_file, str(e))))
            self.printQueueLock.release()
            return 3

#   stop
#       - Purpose:
#           Set a threading event to stop notify this thread to stop.           
    def stop(self):
        self._stop_event.set()

#   run
#       - Purpose:
#           The thread entry point which will run indefinetly and take care of getting poloniex prices and consulting 
#           the trader policy on buy/sell conditions.
    def run(self):

        print('Trader running...')
        startTime = datetime.datetime.now().replace(microsecond=0)
        statusMesg = ""
        candlesticks = []
        recalculateCandlesticksCountDown = 0
        buyPrice = '0.0'
        sellPrice = '0.0'
        currentPrice = '0.0'
        accountBalances = {}
        ordersArePending = False
        tradingState = self.__ACCOUNTS_EMPTY__

        # Check user account balances and determine whether to start by selling or buying. Check if there are open orders.
        try:
            tradingState, ordersArePending, accountBalances = self.__checkState__()
            time.sleep(2)
        except Exception as e:
            #print("Error connecting to Poloniex account: %s" % (str(e)))
            self.printQueueLock.acquire()
            self.printQueue.put(("Error", "Error connecting to Poloniex account: %s" % (str(e))))
            self.printQueueLock.release()
            return 4

        # Begin main loop
        while True:

            # Check if the stop event is set and if so exit
            if self._stop_event.is_set():
                # Do stuff
                return 0

            # Get current bands and ticker price
            try:
                priceCharts = self.__poloniexAPI__.returnTicker()   
                currentPrice = priceCharts[self.__principalCurrency__+'_'+self.__subjectCurrency__]['last']
                # If the trader starts in the sell state, use the current price as the buy price.
                if buyPrice == '0.0':
                    buyPrice = currentPrice

                # Only calculate bands when the candlestick period time interval has passed (ex. 5 minutes)
                recalculateCandlesticksCountDown = recalculateCandlesticksCountDown - self.__request_interval__
                if recalculateCandlesticksCountDown <= 0:
                    candlesticks = self.__getCandleSticks__()
                    recalculateCandlesticksCountDown = int(self.__candlestick_period__)#/2
            except Exception as e:
                self.printQueueLock.acquire()
                self.printQueue.put(("Error", 'Error retrieving poloniex ticker feed: %s' % (str(e))))
                self.printQueueLock.release()
                self.__Logger__.writeFile("Error", 'Error retrieving poloniex ticker feed: %s' %(str(e)))

            args = self.__buildArgs__(priceCharts, sellPrice, buyPrice, candlesticks)

            # If orders are pending, wait until they clear
            if ordersArePending:
                statusMesg = "Waiting for orders to clear"
                try:
                    # If checkState returns ordersArePending as true, the loop will continue until
                    # they have cleared. Once they have cleared, the checkState function will have 
                    # also updated the trading state. The order may fail so this is important so 
                    # the bot does not move on to the next state if the previous state was never 
                    # finished. The account balances display is also updated.
                    previousState = tradingState
                    tradingState, ordersArePending, accountBalances = self.__checkState__()
                    if not ordersArePending and tradingState == previousState:
                        self.__Logger__.writeFile("Order was canceled.")
                    time.sleep(2)
                except Exception as e:
                    self.printQueueLock.acquire()
                    self.printQueue.put(("Error", 'Error retrieving open orders: %s' % (str(e))))
                    self.printQueueLock.release()
                    self.__Logger__.writeFile("Error", 'Error retrieving open orders: %s' % (str(e)))

            # Do this when looking to buy
            elif tradingState == self.__BUY_PHASE__:
                statusMesg = "Looking to Buy"
                if self.__policy_class__.shouldBuy(args):
                    # Try buying
                    try:
                        self.__buyAllIn__(priceCharts)
                        pass
                    except Exception as e:
                        self.printQueueLock.acquire()
                        self.printQueue.put(("Error", 'Tried buying but call failed: %s' % (str(e))))
                        self.printQueueLock.release()
                        self.__Logger__.writeFile("Error Tried buying but call failed: %s" % (str(e)))
                        continue
                    buyPrice = currentPrice
                    statusMesg = "Buying at %s" % (buyPrice)
                    self.__Logger__.writeFile("Bought at %s" % (buyPrice))
                    ordersArePending = True                 

            # Do this when looking to sell 
            elif tradingState == self.__SELL_PHASE__:
                statusMesg = "Looking to Sell (Bought at %s)" % (buyPrice)          
                if self.__policy_class__.shouldSell(args):
                    # Try selling
                    try:
                        self.__sellAllIn__(priceCharts)
                        pass
                    except Exception as e:
                        self.printQueueLock.acquire()
                        self.printQueue.put(("Error", 'Tried selling but call failed: %s' % (str(e))))
                        self.printQueueLock.release()
                        self.__Logger__.writeFile("Error Tried selling but call failed: %s" % (str(e)))
                        continue
                    sellPrice = currentPrice
                    profitPercent = (float(sellPrice)/float(buyPrice) * 100.0) - 100.0
                    statusMesg = "Selling at %s\t\tProfit : %f%%" % (sellPrice, profitPercent)
                    self.__Logger__.writeFile("Sold at %s\tProfit : %f%%" % (sellPrice, profitPercent))
                    self.__policy_class__.cleanUp(args)
                    ordersArePending = True                  

            else:
                    statusMesg = "Account Balance is Empty"     

            # Send status to printer thread
            self.printQueueLock.acquire()
            self.printQueue.put(("Status", statusMesg))
            self.printQueue.put((PrinterThread.TICKER_KEY, accountBalances))
            self.printQueue.put(("Ticker Price", currentPrice))
            self.printQueueLock.release()

            # Use a loop to sleep instead so the sleep times are shorter. This allows the thread
            # to quit sleeping when the user wants to quit the program.
            for i in range(0, self.__request_interval__):
                if self._stop_event.is_set():
                    # Do stuff
                    return 0
                uptime = datetime.datetime.now().replace(microsecond=0) - startTime
                self.printQueueLock.acquire()
                self.printQueue.put(("Uptime", uptime))
                self.printQueueLock.release()
                time.sleep(1)

#   __checkState__
#       - Purpose:
#           Check whether bot should be selling or buying.
#       - Return:
#           (int) 0 : BUY PHASE
#           (int) 1 : SELL_PHASE
#           (int) 2 : ACCOUNTS_EMPTY
    def __checkState__(self):
        state = self.__ACCOUNTS_EMPTY__
        openOrdersStatus = False

        # Check if should be buying or selling.
        # Is based on which account has the highest balance.
        accountBalances = self.__poloniexAPI__.returnBalances()
        balancePrincipal = float(accountBalances['BTC'])
        balanceSubject = float(accountBalances[self.__subjectCurrency__])
        if balancePrincipal > 0.0 and balancePrincipal > balanceSubject:
            state = self.__BUY_PHASE__
        elif balanceSubject > 0.0 and balanceSubject > balancePrincipal:
            state = self.__SELL_PHASE__
        else:
            state = self.__ACCOUNTS_EMPTY__
        
        # Check if there are any open order for the key pair.
        openOrders = self.__poloniexAPI__.returnOpenOrders('BTC_'+self.__subjectCurrency__)
        if bool(openOrders):
            openOrdersStatus = True
        return (state, openOrdersStatus, accountBalances)

#   __buyAllIn__
#       - Purpose:
#           Submit a purchase order for as much of a particular currency as the user can provide (all in).
#       - Parameters:
#           * (currentPrice) A string representation of a number indicating the current ticker price.
#       - Returns:
#           An order receipt dictionary containing the order number.
#       - NOTE:
#           Orders will likely not be instant which needs to be accounted for after this function is called.
#           A the order has not cleared and the bot wants to sell then the sell must be delayed or the order 
#           must be canceled and the bot will look to buy again.
#
#           Add check if no balances are available and throw exception. Need to create custom exception.
    def __buyAllIn__(self, priceCharts):
        tradableBalance = self.__poloniexAPI__.returnCompleteBalances()
        subjectCurrencyCost = priceCharts['BTC_'+self.__subjectCurrency__]['last']
        amount = float(tradableBalance['BTC']['available']) / float(subjectCurrencyCost)
        if bool(Bitbot_CDO.use_immediate_or_cancel_orders):
            orderReceipt = self.__poloniexAPI__.buy('BTC_'+self.__subjectCurrency__, subjectCurrencyCost, str(amount), immediateOrCancel=True)
        else:
            orderReceipt = self.__poloniexAPI__.buy('BTC_'+self.__subjectCurrency__, subjectCurrencyCost, str(amount))
        return orderReceipt

#   __sellAllIn__
#       - Purpose:
#           Submit a sell order for as much of a particular currency as the user can provide (all in).
#       - Parameters:
#           * (currentPrice) A string representation of a number indicating the current ticker price.
#       - Returns:
#           An order receipt dictionary containing the order number.
#       - NOTE:
#           Orders will likely not be instant which needs to be accounted for after this function is called.
#           A the order has not cleared and the bot wants to buy then the buy must be delayed or the order 
#           must be canceled and the bot will look to sell again.
#   
#           Add check if no balances are available and throw exception. Need to create custom exception.
    def __sellAllIn__(self, priceCharts):
        tradableBalance = self.__poloniexAPI__.returnCompleteBalances()
        subjectCurrencyCost = priceCharts['BTC_'+self.__subjectCurrency__]['last']
        amount = tradableBalance[self.__subjectCurrency__]['available']
        if bool(Bitbot_CDO.use_immediate_or_cancel_orders):
            orderReceipt = self.__poloniexAPI__.sell('BTC_'+self.__subjectCurrency__, subjectCurrencyCost, str(amount), immediateOrCancel=True)
        else:
            orderReceipt = self.__poloniexAPI__.sell('BTC_'+self.__subjectCurrency__, subjectCurrencyCost, str(amount))
        return orderReceipt

    # __getCandleSticks__
    #   - Purpose:
    #       Build a poloniex API query and return the resulting candlestick closing history.
    #   - Returns:
    #       An candlestick closing prices, represented as strings, at the specified interval in the config.
    def __getCandleSticks__(self):
        startDate = None
        endDate = datetime.datetime.now()
        if self.__period_unit__ == "DAYS": 
            startDate = (endDate - datetime.timedelta(days=self.__measurement_period__ * 2)).timestamp()
        elif self.__period_unit__ == "HOURS":
            # Calculation needs fixed like minutes
            startDate = (endDate - datetime.timedelta(hours=self.__measurement_period__ * 2)).timestamp()
        elif self.__period_unit__ == "MINUTES":
            startDate = (endDate - datetime.timedelta(minutes=self.__measurement_period__ * (2*(int(self.__candlestick_period__)/60)))).timestamp()
        else:
            self.printQueueLock.acquire()
            self.printQueue.put(("Error", "No Such Period Unit %s".format(self.__period_unit__)))
            self.printQueueLock.release()
            #print("No such period unit %s" % (self.__period_unit__))
            return None

        endDate = endDate.timestamp()
        history = self.__poloniexAPI__.returnChartData(self.__principalCurrency__+'_'+self.__subjectCurrency__, startDate, endDate, self.__candlestick_period__)
        closing_history = []

        for item in history:
            closing_history.append(item['close'])

        return closing_history

    # __buildArgs__
    #   - Purpose:
    #       Build a dictionary of arguments to be passed to a policy class.
    #   - Parameters:
    #       (priceCharts) A dictionary of all current crypto prices and volume data sorted by currency pair.
    #       (sellPrice) The price at which the bot last sold its' crypto.
    #       (buyPrice) The price at which the bot last bought its' crypto.
    #       (candlesticks) An array of candlestick data containing the closing prices of the selected crypto
    #                      at the selected candlestick period/interval.
    #   - Returns:
    #       A dictionary of relevent cryptocurrency data that is to be passed to the policy class.
    def __buildArgs__(self, priceCharts, sellPrice, buyPrice, candlesticks):
        args = {'candle_period' : self.__candlestick_period__,
                'measurement_period' : self.__measurement_period__,
                'period_unit' : self.__period_unit__,
                'currencyPair' : self.__principalCurrency__+'_'+self.__subjectCurrency__,
                'printQueue' : self.printQueue,
                'printQueueLock' : self.printQueueLock,
                'removeQueue' : self.removeQueue,
                'removeQueueLock' : self.removeQueueLock,
                'candlesticks' : candlesticks,
                'priceCharts' : priceCharts,
                'sellPrice' : sellPrice,
                'buyPrice': buyPrice}
        return args
