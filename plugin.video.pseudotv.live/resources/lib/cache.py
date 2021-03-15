#   Copyright (C) 2021 Lunatixz
#
#
# This file is part of PseudoTV Live.
#
# PseudoTV Live is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV Live is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.
# https://github.com/kodi-community-addons/script.module.simplecache/blob/master/README.md
# -*- coding: utf-8 -*-
 
import resources.lib.globals as globals
  
from kodi_six               import xbmc, xbmcaddon
from datetime               import timedelta
from simplecache            import use_cache, SimpleCache
from resources.lib.settings import Settings  

def stringify(serial):
    return globals.dumpJSON(serial)

def serialize(string):
    return globals.loadJSON(string)

def getSettingInt(key):
    return Settings(xbmcaddon.Addon('plugin.video.pseudotv.live')).getSettingInt(key)

def cacheit(life=timedelta(days=getSettingInt('Max_Days'))):
    def decorator(func):
        def decorated(*args, **kwargs):
            method_class = args[0]
            method_class_name = method_class.__class__.__name__
            cache_str = "%s.%s" % (method_class_name, func.__name__)
            for item in args[1:]: cache_str += u".%s"%item
            data = func(*args, **kwargs)
            results = method_class.cache.get(cache_str.lower(), data)
            if results: return results
            return method_class.cache.set(cache_str.lower(), data, life)
        return decorated
    return decorator

class Cache:
    def __init__(self, memory=True):
        self.cache = SimpleCache()
        self.cache.enable_mem_cache = memory
            
            
    def log(self, msg, level=xbmc.LOGDEBUG):
        return globals.log('%s: %s'%(self.__class__.__name__,msg),level)
        
        
    def set(self, name, data, life=timedelta(minutes=15)):
        if not name.startswith(globals.ADDON_ID): name = '%s.%s'%(globals.ADDON_ID,name)
        self.log('set, name = %s'%(name))
        results = self.cache.set(name.lower(), stringify(data), checksum=stringify(data), expiration=life)
        return data
        
    
    def get(self, name, checksum=""):
        if not name.startswith(globals.ADDON_ID): name = '%s.%s'%(globals.ADDON_ID,name)
        self.log('get, name = %s'%(name))
        results = self.cache.get(name.lower(),stringify(checksum))
        if not results: return None
        return serialize(results)