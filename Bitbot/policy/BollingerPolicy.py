
#### BollingerPolicy ####
# This class contains all of the tools needed to calculate Bollinger bands and make a decision on whether or 
# not to buy a coin at the current price.

import math
import pandas as pd
import numpy as np
from lib import Bitbot_CDO
from policy.PolicyTemplate import PolicyTemplate

class BollingerPolicy(PolicyTemplate):

    __HighestPrice__ = 0.0

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
        bollingerBands = BollingerPolicy.__getBollingerBands__(args['candlesticks'], args['measurement_period'])
        currencyPair = args['currencyPair']
        currentPrice = args['priceCharts'][currencyPair]['last']
        printQueue = args['printQueue']
        printQueueLock = args['printQueueLock']
        removeQueue = args['removeQueue']
        removeQueue = args['removeQueueLock']

        priceOverBandPercentage = (float(currentPrice)/float(bollingerBands['lowerband'][-1])*100.0) - 100
        lowerbandGradient = BollingerPolicy.__amplifyGradient__(float(bollingerBands['lowerband'][-1])-float(bollingerBands['lowerband'][-2]))
        upperbandGradient = BollingerPolicy.__amplifyGradient__(float(bollingerBands['upperband'][-1])-float(bollingerBands['upperband'][-2]))
        smaGradient = BollingerPolicy.__amplifyGradient__(float(bollingerBands['sma'][-1])-float(bollingerBands['sma'][-2]))

        printQueueLock.acquire()
        printQueue.put(('Info', 'pobp : %f\tlbg : %f\tubg : %f' % (priceOverBandPercentage, lowerbandGradient, upperbandGradient)))
        printQueueLock.release()

        # Check if price is certain percent above lowerband and lowerband slope is not negative
        #if (priceOverBandPercentage <= float(Bitbot_CDO.lower_band_buy_proximity)) and (lowerbandGradient >= float(Bitbot_CDO.lower_band_sma_minimum_gradient)):
        #    printQueueLock.acquire()
        #    printQueue.put(('Reason', 'Buying for reason (pobp : %.2f) (lbg : %.2f)' % (priceOverBandPercentage, lowerbandGradient)))
        #    printQueueLock.release()
        #    return True
        # Check if upperband slope is positive and sma band slope is positive indicating uptrend
        if (upperbandGradient >= float(Bitbot_CDO.upper_band_sma_minimum_gradient)) and (smaGradient >= float(Bitbot_CDO.upper_band_sma_minimum_gradient)):
            printQueueLock.acquire()
            printQueue.put(('Reason', 'Buying for reason (ubg : %.2f) (smag : %.2f)' % (upperbandGradient, smaGradient)))
            printQueueLock.release()
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
        bollingerBands = BollingerPolicy.__getBollingerBands__(args['candlesticks'], args['measurement_period'])
        currencyPair = args['currencyPair']
        currentPrice = args['priceCharts'][currencyPair]['last']
        buyPrice = args['buyPrice']
        printQueue = args['printQueue']
        printQueueLock = args['printQueueLock']
        removeQueue = args['removeQueue']
        removeQueue = args['removeQueueLock']

        currentPrice = float(currentPrice)
        if currentPrice > BollingerPolicy.__HighestPrice__:
            BollingerPolicy.__HighestPrice__ = currentPrice

        currentDifferenceFromBuy = (((float(currentPrice)/float(buyPrice)*100.0))-100)
        currentDifferenceFromHighest = (100.0-((currentPrice/BollingerPolicy.__HighestPrice__)*100.0))
        lowerbandGradient = BollingerPolicy.__amplifyGradient__(float(bollingerBands['lowerband'][-1])-float(bollingerBands['lowerband'][-2]))
        smaGradient = BollingerPolicy.__amplifyGradient__(float(bollingerBands['sma'][-1])-float(bollingerBands['sma'][-2]))

        printQueueLock.acquire()
        printQueue.put(('Info', 'cdb : %f\tlbg : %f\tsma : %f' % (currentDifferenceFromBuy, lowerbandGradient, smaGradient)))
        printQueueLock.release()

        # If the current price is a certain percentage below the buy price, sell.
        if currentDifferenceFromBuy <= (-1.0 * float(Bitbot_CDO.sell_safety_threshold)):
            printQueueLock.acquire()
            printQueue.put(('Reason', 'Selling for reason (buyDif : %.2f)' % (currentDifferenceFromBuy)))
            printQueueLock.release()
            return True
        # If the current price is a certain percentage below the highest gain price, sell.
        elif currentDifferenceFromHighest >= float(Bitbot_CDO.sell_safety_threshold):
            printQueueLock.acquire()
            printQueue.put(('Reason', 'Selling for reason (highDif : %.2f)' % (currentDifferenceFromHighest)))
            printQueueLock.release()
            return True
        # Check if slope of SMA and lower are negative indicating downtrend
        elif (lowerbandGradient <= float(Bitbot_CDO.lower_band_sma_minimum_gradient)) and (smaGradient <= float(Bitbot_CDO.lower_band_sma_minimum_gradient)):
            printQueueLock.acquire()
            printQueue.put(('Reason', 'Selling for reason (lbg : %.2f) (smag : %.2f)' % (lowerbandGradient, smaGradient)))
            printQueueLock.release()
            return True

        return False

    #   cleanUp
    #       - Purpose:
    #           The policy keeps track of the highest price reached when looking to sell. This should
    #           be cleared (set to 0) after selling.
    def cleanUp(args):
        BollingerPolicy.__HighestPrice__ = 0.0

    # __getBollingerBands__
    #   - Purpose:  
    #       Calculates Bollinger bands based on a dataset of the price history of a coin and returns a dictionary 
    #       containing the sma, upper Bollinger band, and lower Bollinger band.
    #   - Parameters:
    #       * (period) An int dictating the size of the rolling window on the array.
    #   - Returns: 
    #       A dictionary of sma and Bollinger bands
    def __getBollingerBands__(dataset, period):

        dataframe = pd.DataFrame(dataset)
        sma = dataframe.rolling(window=period).mean()
        std = dataframe.rolling(window=period).std()
        upperband = sma + (std * 2)
        lowerband = sma - (std * 2)

        return {'sma' : BollingerPolicy.__makeNormalArray__(sma), 
                'upperband' : BollingerPolicy.__makeNormalArray__(upperband),
                'lowerband' : BollingerPolicy.__makeNormalArray__(lowerband)}

    # __makeNormalArray__ 
    #   - Purpose:  
    #       Converts a Pandas dataframe into a normal python array and removes and NaN values.
    #   - Parameters:   
    #       * (dataframe) a Pandas dataframe  
    #   - Returns:
    #       (array) A python array
    def __makeNormalArray__(dataframe):
        normalArray = []
        dataframe = dataframe.dropna()
        for item in dataframe[0]:
            normalArray.append(item)
        return normalArray

    # __amplifyGradient__
    #   - Purpose:
    #       Calculate an amplifier to be applied to the calculated gradient so it can be compared to the
    #       gradient specified by the user in the config. The function takes a number and determines how
    #       many leading zeroes are present.
    #   - Parameters:
    #       * (gradient) The calculated gradient from the prices.
    #   - Returns
    #       (float) The amplified gradient
    def __amplifyGradient__(gradient):
        amplifier = 1
        # Taking the log of a negative number causes an exception. Take the log of the positive of the number.
        numLeadingZeroes = math.ceil(math.log10(abs(gradient)))

        # numLeadingZeroes will be negative if there are leading zeroes. Get the positive number and 
        # use that instead. If there are no leading zeroes return the gradient.
        if numLeadingZeroes > 0:
            return gradient
        else:
            numLeadingZeroes *= -1

        # Calculate an amplifier to make the gradient greater than 0.
        for i in range(0, numLeadingZeroes+1):
            amplifier *= 10
        return amplifier * gradient
