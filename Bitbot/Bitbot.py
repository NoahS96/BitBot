#!/usr/bin/env python3

import os, sys, queue, threading, time, datetime, curses, signal
from lib import Bitbot_CDO
from lib.PrinterThread import PrinterThread
from lib.TraderThread import TraderThread
from threading import Thread
from configparser import ConfigParser
from policy.BollingerPolicy import BollingerPolicy
from lib.Poloniex import poloniex

# Globals
# Fill the queue with lists of this format (key, value)
__KEY_Q__ = 113
__KEY_Y__ = 121
__KEY_N__ = 110
printQueue = queue.Queue(10)        
printQueueLock = threading.Lock()
removeQueue = queue.Queue(10)
removeQueueLock = threading.Lock()
thread_dict = {"PrinterThread":0, "TraderThread":1}
poloniexAPI = None

# getConfigurations
#   - Purpose:  
#       Read the attributes from bitbot.config into the Bitbot Configuration Data Object
def getConfigurations():

    # Read configurations into Bitbot_CDO
    try:
        configurations = ConfigParser()
        configurations.read('config/bitbot.config')
        for section in configurations.sections():
            for item in list(configurations.items(section)):
                value = configurations.get(section, item[0])
                setattr(Bitbot_CDO, item[0], value)
    except Exception as e:
        print("Error reading properties from bitbot.config: %s" % (str(e)))
        exit(1)

#   sendToQueue
#       - Purpose:
#           Add a key and message if present to one of the printerThreads queue's.
def sendToQueue(queue, lock, key, mesg=None):
    lock.acquire()
    if mesg == None:
        # For remove queue
        queue.put(key)
    else:
        # For print queue
        queue.put((key, mesg))
    lock.release()

# Begin main
def main(): 
    print("Starting Bitbot...")

    # Get the API key and secret from the properties file
    try:
        getConfigurations()
    except Exception as e:
        print('Error reading bitbot.conf: %s' % (str(e)))
    poloniexAPI = poloniex(Bitbot_CDO.api_key, Bitbot_CDO.api_secret)
    enable_visual_mode = bool(Bitbot_CDO.enable_visual_mode)

    # Start the printer thread
    if enable_visual_mode:
        try:
            print('Starting Printer Thread...')
            printerT = PrinterThread(thread_dict["PrinterThread"], "PrinterThread", printQueue, printQueueLock, removeQueue, removeQueueLock)
            printerT.start()
            # Wait for thread to inintialize screen so nobody uses it before it's made.
            while not printerT.screenIsReady():
                pass
        except Exception as e:
            print("Error could not start printer thread: %s" % (str(e)))
            return 1
    else:
        sys.stdout = open(os.devnull, 'w')
    
    # Start the trader thread 
    try:
        print('Starting Trader Thread...')
        traderT = TraderThread(thread_dict["TraderThread"], "TraderThread", printQueue, printQueueLock, removeQueue, removeQueueLock, poloniexAPI)
        traderT.start()
    except Exception as e:
       print("Error could not start trader thread: %s" % (str(e)))
       return 2

    #startTime = datetime.datetime.now().replace(microsecond=0)
    # While loop waiting for key presses 
    while True:
        if enable_visual_mode:
            sendToQueue(printQueue, printQueueLock, PrinterThread.USER_INPUT_KEY, "Press \'q\' to quit")
            keypress = printerT.getChar()
            # The quit key was pressed
            if keypress == __KEY_Q__:
                sendToQueue(printQueue, printQueueLock, PrinterThread.USER_INPUT_KEY, "Are you sure you want to quit? (y\\n)")
                # Double check the user wants to exit
                while True:
                    keypress = printerT.getChar()
                    if keypress == __KEY_Y__:  
                        # Kill the other threads
                        printerT.stop()
                        traderT.stop()
                        printerT.join()
                        print('Printer thread stopped')
                        traderT.join()
                        print('Trader thread stopped')
                        return 0
                    elif keypress == __KEY_N__:
                        sendToQueue(printQueue, printQueueLock, PrinterThread.USER_INPUT_KEY, "Press \'q\' to quit")
                        break
                    elif keypress != 0:
                        sendToQueue(printQueue, printQueueLock, PrinterThread.USER_INPUT_KEY, "Are you sure you want to quit? Select \'y\' or \'n\'")

main()


