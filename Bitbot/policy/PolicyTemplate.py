#### PolicyTemplate ####
# This class acts as an interface/abstract class for implementing a trading policy.
# A custom trading policy must inheret this class and implement the specified functions to work.

class PolicyTemplate(object):

    # shouldBuy
    #   - Purpose:  
    #       Determine whether to buy a cryptocurrency at the current price.
    #   - Parameters:
    #       * (args) A dictionary passed from the TraderThread containing:
    #           { 'candle_period' : self.__candlestick_period__,        
    #            'measurement_period' : self.__measurement_period__,    
    #            'period_unit' : self.__period_unit__,                  
    #            'currency' : self.__currency__,                        
    #            'candlesticks' : candlesticks,                     (list)
    #            'priceCharts' : priceCharts,                       (list)    
    #            'sellPrice' : sellPrice,
    #            'buyPrice': buyPrice }
    #          All dictionary items are represented as strings
    #   - Returns: 
    #       (boolean) Value indicating whether to buy: [True = 'yes'] [False = 'no']
    def shouldBuy(args):
        raise NotImplementedError("Policy function shouldBuy() not implemented")

    # shouldSell
    #   - Purpose:  
    #       Determine whether to sell a cryptocurrency at the current price.
    #   - Parameters:
    #       * (args) A dictionary passed from the TraderThread containing:
    #           { 'candle_period' : self.__candlestick_period__,        
    #            'measurement_period' : self.__measurement_period__,    
    #            'period_unit' : self.__period_unit__,                  
    #            'currency' : self.__currency__,                        
    #            'candlesticks' : candlesticks,                     (list)
    #            'priceCharts' : priceCharts,                       (list)    
    #            'sellPrice' : sellPrice,
    #            'buyPrice': buyPrice }
    #          All dictionary items are represented as strings
    #   - Returns: 
    #       (boolean) Value indicating whether to sell: [True = 'yes'] [False = 'no']
    def shouldSell(args):
        raise NotImplementedError("Policy function shouldSell() not implemented")

    #   cleanUp
    #       - Purpose:
    #           The policy keeps track of the highest price reached when looking to sell. This should
    #           be cleared (set to 0) after selling.
    def cleanUp(args):
        raise NotImplementedError("Policy function cleanUp() not implemented")

    # __getBollingerBands__
    #   - Purpose:  
    #       Calculates Bollinger bands based on a dataset of the price history of a coin and returns a dictionary 
    #       containing the sma, upper Bollinger band, and lower Bollinger band.
    #   - Parameters:
    #       * (period) An int dictating the size of the rolling window on the array.
    #   - Returns: 
    #       A dictionary of sma and Bollinger bands
    def sendToQueue(self, queue, lock, key, mesg=None):
        lock.acquire()
        if not mesg == None:
            queue.put((key, mesg))
        else:
            queue.put(key)
        lock.acquire()
            

