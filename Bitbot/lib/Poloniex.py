import urllib
from urllib.parse import urlencode
from urllib.request import urlopen
import json
import time
import hmac,hashlib

def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))

class poloniex:
    def __init__(self, APIKey, Secret):
        self.APIKey = APIKey
        self.Secret = Secret

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if('return' in after):
            if(isinstance(after['return'], list)):
                for x in xrange(0, len(after['return'])):
                    if(isinstance(after['return'][x], dict)):
                        if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))
                            
        return after

    def api_query(self, command, req={}):

        if(command == "returnTicker" or command == "return24Volume"):
            ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command))
            return json.loads(ret.read().decode('utf-8'))
        elif(command == "returnOrderBook"):
            ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])))
            return json.loads(ret.read().decode('utf-8'))
        elif(command == "returnMarketTradeHistory"):
            ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(req['currencyPair'])))
            return json.loads(ret.read().decode('utf-8'))
        elif(command == "returnChartData"):
            ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])
                + '&start=' + str(req['start']) + '&end=' + str(req['end']) + '&period=' + str(req['period'])))
            return json.loads(ret.read().decode('utf-8'))
        else:
            req['command'] = command
            req['nonce'] = int(time.time()*1000)
            post_data = urllib.parse.urlencode(req)
            post_data = str(post_data).encode('utf-8')
            encoded_sign = str(self.Secret).encode('utf-8')

            sign = hmac.new(encoded_sign, post_data, hashlib.sha512).hexdigest()
            headers = {
                'Sign': sign,
                'Key': self.APIKey
            }

            ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/tradingApi', post_data, headers))
            jsonRet = json.loads(ret.read().decode('utf-8'))
            return self.post_process(jsonRet)


    def returnTicker(self):
        return self.api_query("returnTicker")

    def return24Volume(self):
        return self.api_query("return24Volume")

    def returnOrderBook (self, currencyPair):
        return self.api_query("returnOrderBook", {'currencyPair': currencyPair})

    def returnMarketTradeHistory (self, currencyPair):
        return self.api_query("returnMarketTradeHistory", {'currencyPair': currencyPair})

    def returnChartData (self, currencyPair, startDate, endDate, candlePeriod):
        return self.api_query("returnChartData", {'currencyPair': currencyPair, 'start': startDate, 'end': endDate, 'period': candlePeriod})

    # Returns all of your balances.
    # Outputs: 
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def returnBalances(self):
        return self.api_query('returnBalances')

    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs: 
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def returnOpenOrders(self,currencyPair):
        return self.api_query('returnOpenOrders',{"currencyPair":currencyPair})


    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs: 
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def returnTradeHistory(self,currencyPair):
        return self.api_query('returnTradeHistory',{"currencyPair":currencyPair})

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs: 
    # orderNumber   The order number
    def buy(self,currencyPair,rate,amount, immediateOrCancel=False):
        if immediateOrCancel:
            return self.api_query('buy',{"currencyPair":currencyPair,"rate":rate,"amount":amount,"immediateOrCancel":"1"})
        else:
            return self.api_query('buy',{"currencyPair":currencyPair,"rate":rate,"amount":amount})

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs: 
    # orderNumber   The order number
    def sell(self,currencyPair,rate,amount, immediateOrCancel=False):
        if immediateOrCancel:
            return self.api_query('sell',{"currencyPair":currencyPair,"rate":rate,"amount":amount,"immediateOrCancel":"1"})
        else:
            return self.api_query('sell',{"currencyPair":currencyPair,"rate":rate,"amount":amount})

    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs: 
    # succes        1 or 0
    def cancel(self,currencyPair,orderNumber):
        return self.api_query('cancelOrder',{"currencyPair":currencyPair,"orderNumber":orderNumber})

    # Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method, the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."} 
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs: 
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw',{"currency":currency, "amount":amount, "address":address})
                                                  
    # Returns your current tradable balances for each currency in each market for which margin trading is enabled. Please note that these balances may 
    # vary continually with market conditions.
    # Outputs:
    # {
    #   "BTC_DASH": {
    #       "BTC": "8.50274777",
    #       "DASH": "654.05752077"
    #   },
    #   "BTC_LTC": {
    #       "BTC": "8.50274777",
    #       "LTC": "1214.67825290"
    #   }, 
    #   ...
    # } 
    def returnTradableBalances(self):
        return self.api_query('returnTradableBalances')

        # Returns the current amount you hold of each currency.
    # Outputs:
    # {
    #   "exchange": {
    #       "BTC": "1.19042859",
    #       "BTM": "386.52379392",
    #       "CHA": "0.50000000",
    #       "DASH": "120.00000000",
    #       "STR": "3205.32958001",
    #       "VNL": "9673.22570147"
    #   },
    #   "margin": {
    #       "BTC": "3.90015637",
    #       "DASH": "250.00238240",
    #       "XMR": "497.12028113"
    #   },
    #       "lending": {
    #       "DASH": "0.01174765",
    #       "LTC": "11.99936230"
    #   }
    # }
    def returnAvailableAccountBalances(self):
        return self.api_query('returnAvailableAccountBalances')

    # Returns all of your balances, including available balance, balance on orders, and the estimated BTC value of 
    # your balance. By default, this call is limited to your exchange account; set the "account" POST parameter to 
    # "all" to include your margin and lending accounts.
    # Output:
    # {
    #   "LTC": {
    #       "available": "5.015",
    #       "onOrders": "1.0025",
    #       "btcValue": "0.078"
    #   },
    #   "NXT: {
    #       ...
    #   }
    #   ...
    # }
    def returnCompleteBalances(self):
        return self.api_query('returnCompleteBalances')

    # If you are enrolled in the maker-taker fee schedule, returns your current trading fees and trailing 30-day 
    # volume in BTC. This information is updated once every 24 hours.
    # {
    #   "makerFee": "0.00140000",
    #   "takerFee": "0.00240000",
    #   "thirtyDayVolume": "612.00248891",
    #   "nextTier": "1200.00000000"
    # }
    def returnFeeInfo(self):
        return self.api_query('returnFeeInfo')
