from lib import Bitbot_CDO
import datetime

class Logger(object):
    """Writes to bitbot log file"""

    __log_file__ = './bitbot.log'

    def __init__(self):
        self.__log_file__ = Bitbot_CDO.bitbot_log

    def writeFile(self, mesg):
        with open(self.__log_file__, 'a') as f:
            f.write(str(datetime.datetime.now()) + " " + mesg + '\n')
