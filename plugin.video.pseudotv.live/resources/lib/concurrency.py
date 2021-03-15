  # Copyright (C) 2021 Lunatixz


# This file is part of PseudoTV Live.

# PseudoTV Live is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# PseudoTV Live is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import collections
import resources.lib.globals as globals

from kodi_six  import xbmc
from itertools import repeat
from functools import partial

try:
    from multiprocessing       import cpu_count
    from multiprocessing.pool  import ThreadPool 
    CPU_CORES    = cpu_count()
    ENABLE_POOL  = True
    THREAD_CORES = 2 if CPU_CORES < 2 else CPU_CORES
except: ENABLE_POOL = False
    
try:
    from multiprocessing import Process, Queue
    Queue() # import Queue doesn't raise importError on android, call directly.
except:
    from threading import Thread as Process
    from queue     import Queue
    
Msg = collections.namedtuple('Msg', ['event', 'args'])

class PoolHelper:
    def __init__(self):
        if ENABLE_POOL: 
            self.log("THREAD CORES = " + str(THREAD_CORES))
        else:           
            self.log("ThreadPool Disabled")


    def log(self, msg, level=xbmc.LOGDEBUG):
        return globals.log('%s: %s'%(self.__class__.__name__,msg),level)


    def poolList(self, func, items=None, args=None, kwargs=None, chunksize=None):
        results = []
        if ENABLE_POOL:
            pool = ThreadPool(THREAD_CORES)
            if chunksize is None:
                chunksize, extra = divmod(len(items), THREAD_CORES)
                if extra: chunksize += 1
                if len(items) == 0 or chunksize < 1: chunksize = 1
            self.log("poolList, chunksize = %s"%(chunksize))
              
            try:
                if kwargs:
                    results = pool.imap(partial(func, **kwargs), items, chunksize)
                elif args:
                    results = pool.imap(func, zip(items,repeat(args)), chunksize)
                else:
                    results = pool.imap(func, items, chunksize)
            except Exception as e: 
                self.log("poolList, Failed! " + str(e), xbmc.LOGERROR)
            pool.close()
            pool.join()
            
        else:   
            if kwargs:
                results = (partial(func, **kwargs) for item in items)
            elif args:
                results = (func((item, args)) for item in items)
            else:
                results = (func(item) for item in items)
                
        results = list(filter(None, results))
        self.log("poolList, %s(*%s,**%s) has %s results"%(func.__name__,args,kwargs,len(results)))
        return results
        
        
class BaseWorker(Process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.myQueue   = Queue()
        self.myMonitor = globals.MY_MONITOR


    def log(self, msg, level=xbmc.LOGDEBUG):
        return globals.log('%s: %s'%(self.__class__.__name__,msg),level)


    def send(self, event, *args):
        msg = Msg(event, args)
        self.myQueue.put(msg)


    def dispatch(self, msg):
        event, args = msg
        handler = getattr(self, "do_%s"%event, None)
        if not handler:
            raise NotImplementedError("Process has no handler for [%s]"%event)
        handler(*args)


    def start(self):
        self.log('BaseWorker: starting worker')
        while not self.myMonitor.abortRequested():
            if self.myMonitor.waitForAbort(1):
                self.log('worker aborted')
                break
            elif self.myQueue.empty(): 
                self.log('worker finished')
                break
            msg = self.myQueue.get()
            self.dispatch(msg)
        self.log('worker stopped')