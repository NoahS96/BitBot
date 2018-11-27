#### ZonePolicy ####
# This class contains all of the tools needed to calculate chart zones and make a decision on whether 
# to buy/sell if the current price is one of the outer zones.

import math
import pandas as pd
import numpy as np
from lib import Bitbot_CDO
from policy.PolicyTemplate import PolicyTemplate

class ZonePolicy(PolicyTemplate):

    # shouldBuy
    #   - Purpose:  
    #       Determine whether to buy a cryptocurrency at the current price.
    #   - Parameters:
    #       * (args) A dictionary passed from the TraderThread containing:
    #           { 'candle_period' : self.__candlestick_period__,
    #            'measurement_period' : self.__measurement_period__,
    #            'period_unit' : self.__period_unit__,
    #            'currency' : self.__currency__,
    #            'candlesticks' : candlesticks,
    #            'priceCharts' : priceCharts,
    #            'sellPrice' : sellPrice,
    #            'buyPrice': buyPrice }
    #   - Returns: 
    #       (boolean) Value indicating whether to buy: [True = 'yes'] [False = 'no']
    def shouldBuy(args):
        currencyPair = args['currencyPair']
        currentPrice = args['priceCharts'][currencyPair]['last']
        candlesticks = args['candlesticks']
        printQueue = args['printQueue']
        printQueueLock = args['printQueueLock']
        removeQueue = args['removeQueue']
        removeQueue = args['removeQueueLock']

        dataframe = pd.DataFrame(candlesticks)
        mean = dataframe.mean().values
        std = dataframe.std().values

        upperbox_floor = mean + std
        upperbox_ceil = upperbox_floor + (std * float(Bitbot_CDO.red_zone_height))
        lowerbox_ceil = mean - std
        lowerbox_floor = lowerbox_ceil - (std * float(Bitbot_CDO.red_zone_height))

        printQueueLock.acquire()
        printQueue.put(('uf', upperbox_floor))
        printQueue.put(('lc', lowerbox_ceil))
        printQueue.put(('ut', upperbox_floor + ((upperbox_ceil - upperbox_floor) * float(Bitbot_CDO.red_zone_threshold))))
        printQueue.put(('lt', lowerbox_ceil - ((lowerbox_ceil - lowerbox_floor) * float(Bitbot_CDO.red_zone_threshold))))
        printQueueLock.release()

        if float(currentPrice) >= upperbox_floor + ((upperbox_ceil - upperbox_floor) * float(Bitbot_CDO.red_zone_threshold)):
            return True
        if float(currentPrice) <= lowerbox_ceil - ((lowerbox_ceil - lowerbox_floor) * float(Bitbot_CDO.red_zone_threshold)):
            return True

        return False

    # shouldSell
    #   - Purpose:  
    #       Determine whether to sell a cryptocurrency at the current price.
    #   - Parameters:
    #       * (args) A dictionary passed from the TraderThread containing:
    #           { 'candle_period' : self.__candlestick_period__,
    #            'measurement_period' : self.__measurement_period__,
    #            'period_unit' : self.__period_unit__,
    #            'currency' : self.__currency__,
    #            'candlesticks' : candlesticks,
    #            'priceCharts' : priceCharts,
    #            'sellPrice' : sellPrice,
    #            'buyPrice': buyPrice }
    #   - Returns: 
    #       (boolean) Value indicating whether to sell: [True = 'yes'] [False = 'no']
    def shouldSell(args):
        return True
        raise NotImplementedError("Policy function shouldSell() not implemented")

    #   cleanUp
    #       - Purpose:
    #           The policy keeps track of the highest price reached when looking to sell. This should
    #           be cleared (set to 0) after selling.
    def cleanUp(args):
        return
        raise NotImplementedError("Policy function cleanUp() not implemented")

    # __getBollingerBands__
    #   - Purpose:  
    #       Calculates Bollinger bands based on a dataset of the price history of a coin and returns a dictionary 
    #       containing the sma, upper Bollinger band, and lower Bollinger band.
    #   - Parameters:
    #       * (period) An int dictating the size of the rolling window on the array.
    #   - Returns: 
    #       A dictionary of sma and Bollinger bands
    def sendToQueue(queue, lock, key, mesg=None):
        lock.acquire()
        if not mesg == None:
            queue.put((key, mesg))
        else:
            queue.put(key)
        lock.acquire()
