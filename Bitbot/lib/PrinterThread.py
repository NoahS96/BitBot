#### PrinterThread ####
# This class runs as a thread and is responsible for printing any of the program's information to the screen.
# Any other threads can send data to the printQueue as a key pair (key, value) and the printer will print the key
# as a header and print the value[s] underneath it. 
#
# Issues:
#   - Currently the screen buffer is small and will cause the program to crash if too many lines are printed.
#   - Currently only works on Windows machines.

import time, threading, sys, curses, os, collections

class PrinterThread(threading.Thread):

    __print_dictionary__ = collections.OrderedDict()    # Dictionary will contain what to print
    __print_update_interval__ = 0.5                       # How often the screen will be updated in seconds
    __SCREEN_LINES__ = 20
    __SCREEN_COLS__ = 90
    __KEY_UP__ = 72                     # OS specific key codes
    __KEY_DOWN__ = 80
    TICKER_KEY = "Account Balance"
    USER_INPUT_KEY = "Bitbot"

#   __init__
#       - Parameters:
#           * (threadID) Number identifying this thread
#           * (name) Name identifying this thread
#           * (queue) The queue shared among other threads which this thread will read from
#           * (queueLock) A lock on the printQueue to prevent others from using it when it is being read from
#           * (removeQueue) A queue used to remove entries from the print dictionary. Another thread can put a 
#                           key into this thread and the Printer will remove that key from the dictionary.
#           * (removeQueueLock) A lock on the removeQueue to prevent others from using it.
#       - Purpose:
#           Initialize the class properties.
    def __init__(self, threadID, name, queue, queueLock, removeQueue, removeQueueLock):
       super(PrinterThread, self).__init__()
       self.threadID = threadID
       self.name = name
       self.printQueue = queue
       self.queueLock = queueLock
       self.removeQueue = removeQueue
       self.removeQueueLock = removeQueueLock
       self._stop_event = threading.Event()

#   stop
#       - Purpose:
#           Set a threading event to stop notify this thread to stop.
    def stop(self):
        self._stop_event.set()

#   stopped
#       - Purpose:
#           Allow main thread to check if this thread is stopped.
#       - Returns:
#           Boolean value indicating state.
    def stopped(self):
        return self._stop_event.is_set()

#   getScreen
#       - Purpose:
#           Returns a single character entered into the screen by the user.
#       - Returns:
#           An character code as itype int.
    def getChar(self):
        if self.screenIsReady():
            return self.pad.getch()
        else:
            return 0

#   screenIsReady
#       - Purpose:
#           Return a boolean value indicating if the screen has be initialized yet.
#       - Returns:
#           A boolean flag.
    def screenIsReady(self):
        try:
            temp = self.pad
        except:
            return False
        else:
            return True

#   run
#       - Purpose:
#           The thread entry point which will run indefinetly and take care of printing any information to the screen.
    def run(self):

        ## printScreen
        ##      - Parameters:
        ##          * (stdscr) A curses screen object
        ##      - Purpose: Handles putting the dictionary contents on the screen
        def printScreen(self, stdscr):
            nonlocal scroll
            cursorPosition = 0

            # Iterate through the dictionary and print all key value pairs
            for key in self.__print_dictionary__.keys():
                try:
                    value = self.__print_dictionary__[key]
                except:
                    # If the value is not found we may have removed it so continue to next.
                    continue
                value_type = type(value)
             
                # If the key is the 'ticker balances' then only print the tickers with a balance
                if key == self.TICKER_KEY:
                    stdscr.addstr(cursorPosition, 0, key + ":")
                    cursorPosition += 1
                    for k in value.keys():

                        # Ignore tickers without a balance
                        if not float(value[k]) > 0.0:
                            continue
                        stdscr.addstr(cursorPosition, 4, "{:6} : {:.5f}".format(k, float(value[k])))
                        cursorPosition += 1   
                elif value_type == dict:
                    for k in value.keys():
                        stdscr.addstr(cursorPosition, 4, "{}: {}".format(str(k), str(value[k])))
                        cursorPosition += 1
                else:
                    stdscr.addstr(cursorPosition, 0, "{}: {}".format(key, self.__print_dictionary__[key]))
                    cursorPosition += 1
            # End for
            stdscr.refresh(scroll, 0, 0, 0, self.__SCREEN_LINES__, self.__SCREEN_COLS__)
        # End printScreen


        # Begin run() main
        stdscr = curses.initscr()
        stdscr.scrollok(True)
        stdscr.nodelay(1)
        curses.noecho()
        curses.cbreak()

        # A pad was created earlier to allow for scrolling but as the bot does not currently support
        # this the pad is not needed. Pad will probably be removed later.
        scroll = 0      
        pad = curses.newpad(curses.LINES-1, curses.COLS-1)   
        pad = curses.newpad(self.__SCREEN_LINES__, self.__SCREEN_COLS__)
        pad.refresh(scroll, 0, 0, 0, self.__SCREEN_LINES__, self.__SCREEN_COLS__)
        pad.scrollok(1)
        pad.idlok(1)
        self.pad = pad
        self.stdscrn = stdscr

        while True:

            # Check if this thread is flagged to quit
            if self._stop_event.is_set():
                curses.endwin()
                return 0

            # Get any data updates from the shared queue and add it to the print dictionary
            self.queueLock.acquire()
            if not self.printQueue.empty():
                keyPair = self.printQueue.get()  
                self.queueLock.release()
                key = keyPair[0]
                value = keyPair[1]
                self.__print_dictionary__[key] = value
            else:
                self.queueLock.release()

            # Check if the remove queue has entries and if so get those entries and use them to remove
            # values from the print dictionary.
            self.removeQueueLock.acquire()
            if not self.removeQueue.empty():
                key = self.removeQueue.get()
                self.__print_dictionary__.pop(key)
                self.removeQueueLock.release()
            else:
                self.removeQueueLock.release()

            # Update the screen
            pad.clear()
            printScreen(self, pad)
            time.sleep(self.__print_update_interval__)
        # End while

