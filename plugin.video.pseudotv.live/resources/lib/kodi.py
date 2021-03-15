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

import os
import resources.lib.globals as globals

from kodi_six import xbmc, xbmcgui, xbmcaddon

ADDON_ID      = 'plugin.video.pseudotv.live'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
COLOR_LOGO    = os.path.join(ADDON_PATH,'resources','skins','default','media','logo.png')

class Dialog:
    def __init__(self, dialog=None, progress=0):
        if dialog is None: 
            self.dialog = xbmcgui.Dialog()
        else:
            self.dialog = dialog
            
        self.progress   = progress
        self.onPlayback = globals.getSettingBool('Silent_OnPlayback') #unify silent mode amongst dialogs 
        self.isPlaying  = xbmc.getCondVisibility('Player.Playing')
        self.isOverlay  = globals.isOverlay()
        
                 
    def log(self, msg, level=xbmc.LOGDEBUG):
        return globals.log('%s: %s'%(self.__class__.__name__,msg),level)
    
    
    def okDialog(self, msg, heading=ADDON_NAME):
        return self.dialog.ok(heading, msg)
        
        
    def textviewer(self, msg, heading=ADDON_NAME, usemono=False):
        return self.dialog.textviewer(heading, msg, usemono)
        
    
    def yesnoDialog(self, message, heading=ADDON_NAME, nolabel='', yeslabel='', customlabel='', autoclose=0): 
        if customlabel:
            return self.dialog.yesnocustom(heading, message, customlabel, nolabel, yeslabel, autoclose)
        else: 
            return self.dialog.yesno(heading, message, nolabel, yeslabel, autoclose)


    def notificationDialog(self, message, header=ADDON_NAME, sound=False, time=4000, icon=COLOR_LOGO):
        self.log('notificationDialog: %s'%(message))
        try: 
            return self.dialog.notification(header, message, icon, time, sound=False)
        except Exception as e:
            return xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
             
             
    def selectDialog(self, list, header=ADDON_NAME, preselect=None, useDetails=True, autoclose=0, multi=True):
        if multi == True:
            if preselect is None: preselect = []
            select = self.dialog.multiselect(header, list, autoclose, preselect, useDetails)
        else:
            if preselect is None: preselect = -1
            select = self.dialog.select(header, list, autoclose, preselect, useDetails)
        if select: return select
        return None
      
      
    def inputDialog(self, message, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
        ## - xbmcgui.INPUT_ALPHANUM (standard keyboard)
        ## - xbmcgui.INPUT_NUMERIC (format: #)
        ## - xbmcgui.INPUT_DATE (format: DD/MM/YYYY)
        ## - xbmcgui.INPUT_TIME (format: HH:MM)
        ## - xbmcgui.INPUT_IPADDRESS (format: #.#.#.#)
        ## - xbmcgui.INPUT_PASSWORD (return md5 hash of input, input is masked)
        retval = self.dialog.input(message, default, key, opt, close)
        if retval: return retval
        return None
        
        
    def browseDialog(self, type=0, heading=ADDON_NAME, default='', shares='', mask='', options=None, useThumbs=True, treatAsFolder=False, prompt=True, multi=False, monitor=False):
        if prompt and not default:
            if options is None:
                options  = [{"label":"Video Playlists" , "label2":"Video Playlists"               , "default":"special://profile/playlists/video/" , "mask":'.xsp'             , "type":1, "multi":False},
                            {"label":"Music Playlists" , "label2":"Music Playlists"               , "default":"special://profile/playlists/music/" , "mask":'.xsp'             , "type":1, "multi":False},
                            {"label":"Video"           , "label2":"Video Sources"                 , "default":"library://video/"                   , "mask":globals.VIDEO_EXTS , "type":0, "multi":False},
                            {"label":"Music"           , "label2":"Music Sources"                 , "default":"library://music/"                   , "mask":globals.MUSIC_EXTS , "type":0, "multi":False},
                            {"label":"Pictures"        , "label2":"Picture Sources"               , "default":""                                   , "mask":globals.IMAGE_EXTS , "type":0, "multi":False},
                            {"label":"Files"           , "label2":"File Sources"                  , "default":""                                   , "mask":""                 , "type":0, "multi":False},
                            {"label":"Local"           , "label2":"Local Drives"                  , "default":""                                   , "mask":""                 , "type":0, "multi":False},
                            {"label":"Network"         , "label2":"Local Drives and Network Share", "default":""                                   , "mask":""                 , "type":0, "multi":False},
                            {"label":"Resources"       , "label2":"Resource Plugins"              , "default":"resource://"                        , "mask":""                 , "type":0, "multi":False}]
            listitems = [globals.buildMenuListItem(option['label'],option['label2'],iconImage=COLOR_LOGO) for option in options]

            select    = self.selectDialog(listitems, globals.LANGUAGE(30116), multi=False)
            if select is not None:
                shares    = options[select]['label'].lower().replace("network","")
                mask      = options[select]['mask']
                type      = options[select]['type']
                multi     = options[select]['multi']
                default   = options[select]['default']
        self.log('browseDialog, type = %s, heading= %s, shares= %s, mask= %s, useThumbs= %s, treatAsFolder= %s, default= %s'%(type, heading, shares, mask, useThumbs, treatAsFolder, default))
        if monitor: globals.toggleCHKInfo(True)
        if multi == True:
            ## https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html#ga856f475ecd92b1afa37357deabe4b9e4
            ## type integer - the type of browse dialog.
            ## 1	ShowAndGetFile
            ## 2	ShowAndGetImage
            retval = self.dialog.browseMultiple(type, heading, shares, mask, useThumbs, treatAsFolder, default)
        else:
            ## https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html#gafa1e339e5a98ae4ea4e3d3bb3e1d028c
            ## type integer - the type of browse dialog.
            ## 0	ShowAndGetDirectory
            ## 1	ShowAndGetFile
            ## 2	ShowAndGetImage
            ## 3	ShowAndGetWriteableDirectory
            retval = self.dialog.browseSingle(type, heading, shares, mask, useThumbs, treatAsFolder, default)
        if monitor: globals.toggleCHKInfo(False)
        if retval:
            if prompt and retval == default: return None
            return retval
        return None
        
        
    def notificationProgress(self, message, header=ADDON_NAME, funcs=[], time=4, wait=1):
        dia = self.progressBGDialog(message=message,header=header)
        if funcs: time = len(funcs)
        for i in range(time):
            for func in funcs: func[0](*func[1], **func[2])
            if globals.MY_MONITOR.waitForAbort(wait): break
            dia = self.progressBGDialog((((i + 1) * 100)//time),control=dia,header=header)
        return self.progressBGDialog(100,control=dia)


    def progressBGDialog(self, percent=0, control=None, message='', header=ADDON_NAME):
        if (self.onPlayback & self.isOverlay & self.isPlaying):
            if control is None: return
            else: return control.close()
        if control is None and percent == 0:
            control = xbmcgui.DialogProgressBG()
            control.create(header, message)
        elif control:
            if percent == 100 or control.isFinished(): return control.close()
            else: control.update(percent, header, message)
        return control