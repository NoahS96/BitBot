#### PolicyTemplate ####
# This class acts as an interface/abstract class for implementing a trading policy.
# A custom trading policy must inheret this class and implement the specified functions to work.

class PolicyTemplate(object):

    def shouldBuy(self, args):
        raise NotImplementedError("Policy function shouldBuy() not implemented")

    def shouldSell(self, args):
        raise NotImplementedError("Policy function shouldSell() not implemented")

    def cleanUp(self, args):
        raise NotImplementedError("Policy function cleanUp() not implemented")

    def sendToQueue(self, queue, lock, key, mesg=None):
        lock.acquire()
        if not mesg == None:
            queue.put((key, mesg))
        else:
            queue.put(key)
        lock.acquire()
            

