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

import os, json, traceback

from kodi_six  import xbmc, xbmcgui, xbmcaddon
from resources.lib.concurrency import PoolHelper

ADDON_ID      = 'plugin.video.pseudotv.live'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
COLOR_LOGO    = os.path.join(ADDON_PATH,'resources','skins','default','media','logo.png')

def dumpJSON(item):
    try:    return json.dumps(item)
    except: return ''
    
def loadJSON(item):
    try:    return json.loads(item)
    except: return {}
    
def log(msg, level=xbmc.LOGDEBUG):
    if not REAL_SETTINGS.getSetting('Enable_Debugging') == "true" and level != xbmc.LOGERROR: return
    if not isinstance(msg,str): msg = str(msg)
    if level == xbmc.LOGERROR: msg = '%s\n%s'%((msg),traceback.format_exc())
    xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg),level)

class Settings:
    realSetting = REAL_SETTINGS
    
    def __init__(self, refresh=False):
        if refresh: 
            REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
            self.realSetting = REAL_SETTINGS

         
    def log(self, msg, level=xbmc.LOGDEBUG):
        log('%s: %s'%(self.__class__.__name__,msg),level)
    
    
    def getSettingRefresh(self, key):
        return xbmcaddon.Addon(id=ADDON_ID).getSetting(key)


    def _getSetting(self, func, key):
        try:
            value = func(key)
            self.log('%s, key = %s, value = %s'%(func.__name__,key,value))
            return value
        except Exception as e: 
            self.log("_getSetting, Failed! %s"%(e), xbmc.LOGERROR)


    def getSetting(self, key):
        return self._getSetting(self.realSetting.getSetting,key)
        
        
    def getSettingsList(self, key):
        return self.getSetting(key).split('|')
    
    
    def getSettingsDict(self, key):
        return loadJSON(self.getSetting(key))
    
    
    def getSettingBool(self, key):
        try:    return self._getSetting(self.realSetting.getSettingBool,key)
        except: return self._getSetting(self.realSetting.getSetting,key).lower() == "true" 
        
        
    def getSettingInt(self, key):
        try: return self._getSetting(self.realSetting.getSettingInt,key)
        except:
            value = self._getSetting(self.realSetting.getSetting,key)
            if value.isdecimal():
                return float(value)
            elif value.isdigit(): 
                return int(value)
              
              
    def getSettingNumber(self, key): 
        try: return self._getSetting(self.realSetting.getSettingNumber,key)
        except:
            value = self._getSetting(self.realSetting.getSetting,key)
            if value.isdecimal():
                return float(value)
            elif value.isdigit(): 
                return int(value)    
        
        
    def getSettingString(self, key):     
        return self._getSetting(self.realSetting.getSettingString,key)
        
        
    def openSettings(self):     
        self.realSetting.openSettings()
    

    def _setSetting(self, func, key, value):
        try:
            self.log('%s, key = %s, value = %s'%(func.__name__,key,value))
            func(key, value)
        except Exception as e: 
            self.log("_setSetting, Failed! %s"%(e), xbmc.LOGERROR)
        
        
    def setSetting(self, key, value=""):  
        if not isinstance(value,str): value = str(value)
        self._setSetting(self.realSetting.setSetting,key,value)
            
            
    def setSettingsDict(self, key, values):
        self.setSetting(key, dumpJSON(values))
            
            
    def setSettingsList(self, key, values):
        self.setSetting(key, '|'.join(values))
        
        
    def setSettingBool(self, key, value):  
        if not isinstance(value,bool): value = value.lower() == "true"
        self._setSetting(self.realSetting.setSettingBool,key,value)
        
        
    def setSettingInt(self, key, value):  
        if not isinstance(value,int): value = int(value)
        self._setSetting(self.realSetting.setSettingInt,key,value)
        
        
    def setSettingNumber(self, key, value):  
        if not isinstance(value,float): value = float(value)
        self._setSetting(self.realSetting.setSettingNumber,key,value)
        
        
    def setSettingString(self, key, value):  
        if not isinstance(value,str): value = str(value)
        self._setSetting(self.realSetting.setSettingString,key,value)
        
        
class Properties:
    def __init__(self, winID=10000):
        self.winID  = winID
        self.window = xbmcgui.Window(winID)


    def log(self, msg, level=xbmc.LOGDEBUG):
        log('%s: %s'%(self.__class__.__name__,msg),level)


    def getKey(self, key):
        if self.winID == 10000: #create unique id 
            return '%s.%s'%(ADDON_ID,key)
        else:
            return key


    def clearProperties(self):
        return self.window.clearProperties()
        
        
    def clearProperty(self, key):
        return self.window.clearProperty(self.getKey(key))


    def getProperties(self, key):
        return self.getProperty(key).split('|')

        
    def getPropertyBool(self, key):
        return self.getProperty(key).lower() == "true"
        
        
    def getPropertyDict(self, key):
        return loadJSON(self.getProperty(key))
        
        
    def getPropertyInt(self, key):
        value = self.getProperty(key)
        if value.isdigit(): return int(value)
        return value


    def getProperty(self, key):
        value = self.window.getProperty(self.getKey(key))
        self.log('getProperty, id = %s, key = %s, value = %s'%(self.winID,self.getKey(key),value))
        return value
        
        
    def clearEXTProperty(self, key):
        return self.window.clearProperty(key)
        
        
    def getEXTProperty(self, key):
        return self.window.getProperty(key)
        
        
    def setEXTProperty(self, key, value):
        if not isinstance(value,str): value = str(value)
        return self.window.setProperty(key,value)
        
        
    def setProperties(self, key, values):
        return self.setProperty(key, '|'.join(values))
        
        
    def setPropertyBool(self, key, value):
        if not isinstance(value,bool): value = value.lower() == "true"
        return self.setProperty(key, value)
        
        
    def setPropertyDict(self, key, value):
        return self.setProperty(key, dumpJSON(value))
        
        
    def setProperty(self, key, value):
        if not isinstance(value,str): value = str(value)
        self.log('setProperty, id = %s, key = %s, value = %s'%(self.winID,self.getKey(key),value))
        self.window.setProperty(self.getKey(key), value)
        return True


class Dialog:
    monitor    = xbmc.Monitor()
    settings   = Settings()
    properties = Properties()
    pool       = PoolHelper()
    
    def __init__(self):
        self.onPlayback = self.settings.getSettingBool('Silent_OnPlayback') #unify silent mode amongst dialogs 
        self.isPlaying  = xbmc.getCondVisibility('Player.Playing')
        self.isOverlay  = self.properties.getPropertyBool('OVERLAY')
        
                 
    def log(self, msg, level=xbmc.LOGDEBUG):
        log('%s: %s'%(self.__class__.__name__,msg),level)
    
    
    def toggleCHKInfo(self, state):
        self.properties.setProperty('chkInfo',str(state))
        if state: self.properties.clearProperty('monitor.montiorList')
        else: self.properties.clearProperty('chkInfo')
        
        
    @staticmethod
    def buildItemListItem(item, mType='video', oscreen=True, playable=True):
        LISTITEM_TYPES = {'label': (str,list),'genre': (str,list),
                          'country': (str,list),'year': int,'episode': int,
                          'season': int,'sortepisode': int,'sortseason': int,
                          'episodeguide': str,'showlink': (str,list),'top250': int,
                          'setid': int,'tracknumber': int,'rating': float,'userrating': int,
                          'playcount': int,'overlay': int,'cast': list,'castandrole': list,
                          'director': (str,list),'mpaa': str,'plot': str,'plotoutline': str,
                          'title': str,'originaltitle': str,'sorttitle': str,'duration': int,
                          'studio': (str,list),'tagline': str,'writer': (str,list),'tvshowtitle': str,
                          'premiered': str,'status': str,'set': str,'setoverview': str,'tag': (str,list),
                          'imdbnumber': str,'code': str,'aired': str,'credits': (str,list),'lastplayed': str,
                          'album': str,'artist': list,'votes': str,'path': str,'trailer': str,'dateadded': str,
                          'mediatype': str,'dbid': int}

        info       = item.copy()
        art        = info.pop('art'             ,{})
        streamInfo = item.pop('streamdetails'   ,{})
        properties = info.pop('customproperties',{})
        properties.update(info.get('citem'      ,{}))

        uniqueid   = info.pop('uniqueid'        ,{})
        cast       = info.pop('cast'            ,[])

        def cleanInfo(info):
            tmpInfo = info.copy()
            for key, value in tmpInfo.items():
                ptype = LISTITEM_TYPES.get(key,None)
                if ptype is None: # key not in json enum, move to custom properties
                    info.pop(key)
                    properties[key] = value
                    continue
                if not isinstance(value, ptype):
                    if isinstance(ptype,tuple):
                        ptype = ptype[0]
                    info[key] = ptype(value)
            return info
                
        def cleanProp(cpvalue):
            if isinstance(cpvalue,(dict,list)):
                return dumpJSON(cpvalue)
            return str(cpvalue)
                
        listitem = xbmcgui.ListItem(offscreen=oscreen)
        listitem.setLabel(info.get('label',''))
        listitem.setLabel2(info.get('label2',''))
        listitem.setPath(item.get('file','')) # (item.get('file','') or item.get('url','') or item.get('path',''))
        listitem.setInfo(type=mType, infoLabels=cleanInfo(info))
        listitem.setArt(art)
        listitem.setCast(cast)
        listitem.setUniqueIDs(uniqueid)
        [listitem.setProperty(key, cleanProp(pvalue)) for key, pvalue in properties.items()]
        [listitem.addStreamInfo(key, svalue) for key, svalues in streamInfo.items() for svalue in svalues]
        if playable: listitem.setProperty("IsPlayable","true")
        return listitem
             
        
        
    def okDialog(self, msg, heading=ADDON_NAME):
        return xbmcgui.Dialog().ok(heading, msg)
        
        
    def textviewer(self, msg, heading=ADDON_NAME, usemono=False):
        return xbmcgui.Dialog().textviewer(heading, msg, usemono)
        
    
    def yesnoDialog(self, message, heading=ADDON_NAME, nolabel='', yeslabel='', customlabel='', autoclose=0): 
        if customlabel:
            return xbmcgui.Dialog().yesnocustom(heading, message, customlabel, nolabel, yeslabel, autoclose)
        else: 
            return xbmcgui.Dialog().yesno(heading, message, nolabel, yeslabel, autoclose)


    def notificationDialog(self, message, header=ADDON_NAME, sound=False, time=4000, icon=COLOR_LOGO):
        self.log('notificationDialog: %s'%(message))
        ## - Builtin Icons:
        ## - xbmcgui.NOTIFICATION_INFO
        ## - xbmcgui.NOTIFICATION_WARNING
        ## - xbmcgui.NOTIFICATION_ERROR
        try: 
            xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
        except Exception as e:
            xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
        return True
             
             
    def selectDialog(self, list, header=ADDON_NAME, preselect=None, useDetails=True, autoclose=0, multi=True):
        if multi == True:
            if preselect is None: preselect = [-1]
            select = xbmcgui.Dialog().multiselect(header, list, autoclose, preselect, useDetails)
        else:
            if preselect is None: preselect = -1
            select = xbmcgui.Dialog().select(header, list, autoclose, preselect, useDetails)
        return select
      
      
    def inputDialog(self, message, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
        ## - xbmcgui.INPUT_ALPHANUM (standard keyboard)
        ## - xbmcgui.INPUT_NUMERIC (format: #)
        ## - xbmcgui.INPUT_DATE (format: DD/MM/YYYY)
        ## - xbmcgui.INPUT_TIME (format: HH:MM)
        ## - xbmcgui.INPUT_IPADDRESS (format: #.#.#.#)
        ## - xbmcgui.INPUT_PASSWORD (return md5 hash of input, input is masked)
        retval = xbmcgui.Dialog().input(message, default, key, opt, close)
        if retval: return retval
        return None
        
        
    def buildMenuListItem(self, label1="", label2="", iconImage=None, url="", infoItem=None, artItem=None, propItem=None, oscreen=False, mType='video'):
        listitem  = xbmcgui.ListItem(label1, label2, path=url, offscreen=oscreen)
        iconImage = (iconImage or COLOR_LOGO)
        if propItem: listitem.setProperties(propItem)
        if infoItem: listitem.setInfo(mType, infoItem)
        else: 
            listitem.setInfo(mType, {'mediatype': 'video',
                                     'Label' : label1,
                                     'Label2': label2,
                                     'Title' : label1})
                                         
        if artItem: listitem.setArt(artItem)
        else: 
            listitem.setArt({'thumb': iconImage,
                             'logo' : iconImage,
                             'icon' : iconImage})
        return listitem
        
        
    def browseDialog(self, type=0, heading=ADDON_NAME, default='', shares='', mask='', options=None, useThumbs=True, treatAsFolder=False, prompt=True, multi=False, monitor=False):
        def buildMenuItem(option):
            return self.buildMenuListItem(option['label'],option['label2'],iconImage=COLOR_LOGO)
            
        if prompt and not default:
            if options is None:
                options  = [{"label":"Video Playlists" , "label2":"Video Playlists"               , "default":"special://videoplaylists/"          , "mask":'.xsp'                            , "type":1, "multi":False},
                            {"label":"Music Playlists" , "label2":"Music Playlists"               , "default":"special://musicplaylists/"          , "mask":'.xsp'                            , "type":1, "multi":False},
                            {"label":"Video"           , "label2":"Video Sources"                 , "default":"library://video/"                   , "mask":xbmc.getSupportedMedia('video')   , "type":0, "multi":False},
                            {"label":"Music"           , "label2":"Music Sources"                 , "default":"library://music/"                   , "mask":xbmc.getSupportedMedia('music')   , "type":0, "multi":False},
                            {"label":"Pictures"        , "label2":"Picture Sources"               , "default":""                                   , "mask":xbmc.getSupportedMedia('picture') , "type":0, "multi":False},
                            {"label":"Files"           , "label2":"File Sources"                  , "default":""                                   , "mask":""                                , "type":0, "multi":False},
                            {"label":"Local"           , "label2":"Local Drives"                  , "default":""                                   , "mask":""                                , "type":0, "multi":False},
                            {"label":"Network"         , "label2":"Local Drives and Network Share", "default":""                                   , "mask":""                                , "type":0, "multi":False},
                            {"label":"Resources"       , "label2":"Resource Plugins"              , "default":"resource://"                        , "mask":""                                , "type":0, "multi":False}]
            
            listitems = self.pool.poolList(buildMenuItem,options)
            select    = self.selectDialog(listitems, LANGUAGE(30116), multi=False)
            if select is not None:
                # if options[select]['default'] == "resource://": #TODO PARSE RESOURCE JSON, LIST PATHS
                    # listitems = self.pool.poolList(buildMenuItem,options)
                    # select    = self.selectDialog(listitems, LANGUAGE(30116), multi=False)
                    # if select is not None:
                # else:    
                shares    = options[select]['label'].lower().replace("network","")
                mask      = options[select]['mask']
                type      = options[select]['type']
                multi     = options[select]['multi']
                default   = options[select]['default']
            
        self.log('browseDialog, type = %s, heading= %s, shares= %s, mask= %s, useThumbs= %s, treatAsFolder= %s, default= %s'%(type, heading, shares, mask, useThumbs, treatAsFolder, default))
        if monitor: self.toggleCHKInfo(True)
        if multi == True:
            ## https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html#ga856f475ecd92b1afa37357deabe4b9e4
            ## type integer - the type of browse dialog.
            ## 1	ShowAndGetFile
            ## 2	ShowAndGetImage
            retval = xbmcgui.Dialog().browseMultiple(type, heading, shares, mask, useThumbs, treatAsFolder, default)
        else:
            ## https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html#gafa1e339e5a98ae4ea4e3d3bb3e1d028c
            ## type integer - the type of browse dialog.
            ## 0	ShowAndGetDirectory
            ## 1	ShowAndGetFile
            ## 2	ShowAndGetImage
            ## 3	ShowAndGetWriteableDirectory
            retval = xbmcgui.Dialog().browseSingle(type, heading, shares, mask, useThumbs, treatAsFolder, default)
        if monitor: self.toggleCHKInfo(False)
        if retval:
            if prompt and retval == default: return None
            return retval
        return None
        
        
    def notificationProgress(self, message, header=ADDON_NAME, wait=4):
        dia = self.progressBGDialog(message=message,header=header)
        for idx in range(wait):
            dia = self.progressBGDialog((((idx) * 100)//wait),control=dia,header=header)
            if self.monitor.waitForAbort(1): break
        return self.progressBGDialog(100,control=dia)


    def progressBGDialog(self, percent=0, control=None, message='', header=ADDON_NAME):
        if not isinstance(percent,int): percent = int(percent)
        if (self.onPlayback & self.isOverlay & self.isPlaying):
            if control is None: 
                return False
            else: 
                control.close()
                return True
        elif control is None and percent == 0:
            control = xbmcgui.DialogProgressBG()
            control.create(header, message)
        elif control:
            if percent == 100 or control.isFinished(): 
                control.close()
                return True
            else: control.update(percent, header, message)
        return control
        

    def progressDialog(self, percent=0, control=None, message='', header=ADDON_NAME):
        if not isinstance(percent,int): percent = int(percent)
        if control is None and percent == 0:
            control = xbmcgui.DialogProgress()
            control.create(header, message)
        elif control:
            if percent == 100 or control.isFinished(): 
                control.close()
                return True
            else: control.update(percent, header, message)
        elif control.iscanceled():
            control.close()
            return True
        return control
        
        
class ListItems:
    def __init__(self):
        pass
