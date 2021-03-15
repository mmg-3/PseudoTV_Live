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
# -*- coding: utf-8 -*-

import resources.lib.globals as globals

from kodi_six import xbmc, xbmcgui

class Settings:
    def __init__(self, addon):
        self.SETTINGS = addon

         
    def log(self, msg, level=xbmc.LOGDEBUG):
        return globals.log('%s: %s'%(self.__class__.__name__,msg),level)
    

    def getSettings(self, key):
        return self.getSetting(key).split('|')
    
    
    def getSetting(self, key):
        value = self.SETTINGS.getSetting(key)
        self.log('getSetting, key = %s, value = %s'%(key,value))
        return value
        
        
    def getSettingBool(self, key):
        try:    return self.SETTINGS.getSettingBool(key)
        except: return self.getSetting(key).lower() == "true" 
        
        
    def getSettingInt(self, key):
        try: return self.SETTINGS.getSettingInt(key)
        except:
            value = self.getSetting(key)
            if value.isdecimal():
                return float(value)
            elif value.isdigit(): 
                return int(value)
              
              
    def getSettingNumber(self, key): 
        try: return self.SETTINGS.getSettingNumber(key)
        except:
            value = self.getSetting(key)
            if value.isdecimal():
                return float(value)
            elif value.isdigit(): 
                return int(value)    
        
        
    def getSettingString(self, key):     
        return self.SETTINGS.getSettingString(key)
        
        
    def openSettings(self):     
        return self.SETTINGS.openSettings()
    
    
    def setSettings(self, key, values):
        return self.setSetting(key, '|'.join(values))
        
    
    def setSetting(self, key, value):  
        self.log('setSetting, key = %s, value = %s'%(key,value))
        if not isinstance(value,str): value = str(value)
        return self.SETTINGS.setSetting(key, value)
        
        
    def setSettingBool(self, key, value):  
        if not isinstance(value,bool): value = value.lower() == "true"
        return self.SETTINGS.setSettingBool(key, value)
        
        
    def setSettingInt(self, key, value):  
        if not isinstance(value,int): value = int(value)
        return self.SETTINGS.setSettingInt(key, value)
        
        
    def setSettingNumber(self, key, value):  
        if not isinstance(value,float): value = float(value)
        return self.SETTINGS.setSettingNumber(key, value)
        
        
    def setSettingString(self, key, value):  
        if not isinstance(value,str): value = str(value)
        return self.SETTINGS.setSettingString(key, value)
        
        
class Properties:
    def __init__(self, winID=10000):
        self.winID  = winID
        self.WINDOW = xbmcgui.Window(winID)


    def log(self, msg, level=xbmc.LOGDEBUG):
        return globals.log('%s: %s'%(self.__class__.__name__,msg),level)


    def getKey(self, key):
        if self.winID == 10000: 
            return '%s.%s'%(globals.ADDON_ID,key)
        else:
            return key


    def clearProperties(self):
        return self.WINDOW.clearProperties()
        
        
    def clearProperty(self, key):
        return self.WINDOW.clearProperty(self.getKey(key))


    def getProperties(self, key):
        return self.getProperty(key).split('|')

        
    def getPropertyBool(self, key):
        return self.getProperty(key).lower() == "true"


    def getProperty(self, key):
        value = self.WINDOW.getProperty(self.getKey(key))
        self.log('getProperty, id = %s, key = %s, value = %s'%(self.winID,self.getKey(key),value))
        return value
        
        
    def setProperties(self, key, values):
        return self.setProperty(key, '|'.join(values))
        
        
    def setPropertyBool(self, key, value):
        return self.setProperty(key, value)
        
        
    def setProperty(self, key, value):
        self.log('setProperty, id = %s, key = %s, value = %s'%(self.winID,self.getKey(key),value))
        if not isinstance(value,globals.basestring): value = str(value)
        return self.WINDOW.setProperty(self.getKey(key), value)