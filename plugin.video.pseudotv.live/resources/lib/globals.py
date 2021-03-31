#   Copyright (C) 2020 Lunatixz
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

import os, sys, re, struct, shutil, traceback, threading
import datetime, time, _strptime, base64, binascii, random, hashlib
import json, codecs, collections, uuid

from kodi_six                  import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode
from itertools                 import repeat, cycle, chain, zip_longest
from six.moves                 import urllib
from contextlib                import contextmanager
from simplecache               import use_cache, SimpleCache
from xml.dom.minidom           import parse, parseString, Document
from xml.etree.ElementTree     import ElementTree, Element, SubElement, tostring, XMLParser
from resources.lib.fileaccess  import FileAccess, FileLock
from operator                  import itemgetter
    
try:
    from multiprocessing       import cpu_count
    from multiprocessing.pool  import ThreadPool 
    ENABLE_POOL  = True
    THREAD_CORES = cpu_count()
except: ENABLE_POOL = False
    
try:
    from multiprocessing import Process, Queue
    Queue() # Queue doesn't raise importError on android, call directly.
except:
    from threading import Thread as Process
    from queue     import Queue

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY3: 
    basestring = str
    unicode = str
    
# Plugin Info
ADDON_ID            = 'plugin.video.pseudotv.live'
REAL_SETTINGS       = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME          = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC        = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH          = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION       = REAL_SETTINGS.getAddonInfo('version')
ICON                = REAL_SETTINGS.getAddonInfo('icon')
FANART              = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE            = REAL_SETTINGS.getLocalizedString

MY_MONITOR          = xbmc.Monitor()
MY_PLAYER           = xbmc.Player()

OVERLAY_FLE         = "%s.overlay.xml"%(ADDON_ID)
CHANNELFLE_DEFAULT  = os.path.join(ADDON_PATH,'channels.json')
LIBRARYFLE_DEFAULT  = os.path.join(ADDON_PATH,'library.json')
GENREFLE_DEFAULT    = os.path.join(ADDON_PATH,'genres.xml')
SETTINGS_FLE        = os.path.join(SETTINGS_LOC,'settings.xml')
CHANGELOG_FLE       = os.path.join(ADDON_PATH,'changelog.txt')
VIDEO_EXTS          = xbmc.getSupportedMedia('video')
MUSIC_EXTS          = xbmc.getSupportedMedia('music')
IMAGE_EXTS          = xbmc.getSupportedMedia('picture')
LOGO_EXTS           = ['.png','.jpg','.gif']

IMAGE_LOC           = os.path.join(ADDON_PATH,'resources','images')
MEDIA_LOC           = os.path.join(ADDON_PATH,'resources','skins','default','media')
COLOR_LOGO          = os.path.join(MEDIA_LOC,'logo.png')
MONO_LOGO           = os.path.join(MEDIA_LOC,'wlogo.png')

PVR_CLIENT          = 'pvr.iptvsimple'
PVR_MANAGER         = 'service.iptv.manager'
LANG                = 'en' #todo
DTFORMAT            = '%Y%m%d%H%M%S'
DTZFORMAT           = '%Y%m%d%H%M%S +%z'
DEFAULT_ENCODING    = 'utf-8'

MAX_IMPORT          = 5
EPG_HRS             = 10800  # 3hr in Secs., Min. EPG guidedata
RADIO_ITEM_LIMIT    = 250
CLOCK_SEQ           = 70420
UPDATE_OFFSET       = 3600 #1hr in secs.
UPDATE_WAIT         = 10800.0 # 3hr in Secs.
AUTOTUNE_LIMIT      = 3 #auto items per type.
CHANNEL_LIMIT       = 999
OVERLAY_DELAY       = 15 #secs
CHAN_TYPES          = [LANGUAGE(30002),LANGUAGE(30003),LANGUAGE(30004),LANGUAGE(30005),LANGUAGE(30007),LANGUAGE(30006),LANGUAGE(30080),LANGUAGE(30026),LANGUAGE(30097),LANGUAGE(30033)]
GROUP_TYPES         = ['Addon', 'Directory', 'Favorites', 'Mixed', LANGUAGE(30006), 'Mixed Movies', 'Mixed TV', LANGUAGE(30005), LANGUAGE(30007), 'Movies', 'Music', LANGUAGE(30097), 'Other', 'PVR', 'Playlist', 'Plugin', 'Radio', LANGUAGE(30026), 'Smartplaylist', 'TV', LANGUAGE(30004), LANGUAGE(30002), LANGUAGE(30003), 'UPNP', 'IPTV']
BCT_TYPES           = ['bumpers','ratings','commercials','trailers']
PRE_ROLL            = ['bumpers','ratings']
POST_ROLL           = ['commercials','trailers']

# jsonrpc
ART_PARAMS          = ["thumb","icon","poster","fanart","banner","landscape","clearart","clearlogo"]
JSON_FILE_ENUM      = ["title","artist","albumartist","genre","year","rating","album","track","duration","comment","lyrics","musicbrainztrackid","musicbrainzartistid","musicbrainzalbumid","musicbrainzalbumartistid","playcount","fanart","director","trailer","tagline","plot","plotoutline","originaltitle","lastplayed","writer","studio","mpaa","cast","country","imdbnumber","premiered","productioncode","runtime","set","showlink","streamdetails","top250","votes","firstaired","season","episode","showtitle","thumbnail","file","resume","artistid","albumid","tvshowid","setid","watchedepisodes","disc","tag","art","genreid","displayartist","albumartistid","description","theme","mood","style","albumlabel","sorttitle","episodeguide","uniqueid","dateadded","size","lastmodified","mimetype","specialsortseason","specialsortepisode","sortartist","musicbrainzreleasegroupid","isboxset","totaldiscs","disctitle","releasedate","originaldate","bpm","bitrate","samplerate","channels","datemodified","datenew","customproperties"]
JSON_METHOD         = ["none","label","date","size","file","path","drivetype","title","track","time","artist","album","albumtype","genre","country","year","rating","votes","top250","programcount","playlist","episode","season","totalepisodes","watchedepisodes","tvshowstatus","showtitle","tvshowtitle","sorttitle","productioncode","mpaa","studio","dateadded","lastplayed","playcount","listeners","bitrate","random"] 
JSON_ORDER          = ['ascending','descending']
JSON_OPERATORS      = ["contains","doesnotcontain","is","isnot","startswith","endswith","greaterthan","lessthan","true","false"]
JSON_RETURN_TYPES   = {'album':str,'albumartist':list,'albumartistid':list,'albumid':int,'albumlabel':str,'album':str,'albumstatus':str,'bitrate':int,'bpm':int,'cast':list,'channels':int,'comment':str,'compilation':bool,'contributors':str,'country':list,'customproperties':dict,'description':str,'disc':int,'disctitle':str,'displaycomposer':str,'displayconductor':str,'displaylyricist':str,'displayorchestra':str,'duration':int,'dynpath':str,'episode':int,'episodeguide':str,'firstaired':str,'id':int,'imdbnumber':str,'isboxset':bool,'lyrics':str,'mediapath':str,'mood':list,'mpaa':str,'musicbrainzartistid':list,'musicbrainztrackid':str,'originaldate':str,'originaltitle':str,'plotoutline':str,'premiered':str,'productioncode':str,'releasedate':str,'album':str,'samplerate':int,'season':int,'set':str,'setid':int,'showlink':list,'showtitle':str,'sorttitle':str,'specialsortepisode':int,'specialsortseason':int,'stu]dio':list,'style':list,'tag':list,'tagline':str,'theme':list,'top250':int,'totaldiscs':int,'track':int,'trailer':str,'tvshowid':int,'type':str,'uniqueid':int,'votes':str,'watchedepisodes':int,'writer':list}
LISTITEM_TYPES      = {'label': (str,list),'genre': (str,list),'country': (str,list),'year': int,'episode': int,'season': int,'sortepisode': int,'sortseason': int,'episodeguide': str,'showlink': (str,list),'top250': int,'setid': int,'tracknumber': int,'rating': float,'userrating': int,'playcount': int,'overlay': int,'cast': list,'castandrole': list,'director': (str,list),'mpaa': str,'plot': str,'plotoutline': str,'title': str,'originaltitle': str,'sorttitle': str,'duration': int,'studio': (str,list),'tagline': str,'writer': (str,list),'tvshowtitle': str,'premiered': str,'status': str,'set': str,'setoverview': str,'tag': (str,list),'imdbnumber': str,'code': str,'aired': str,'credits': (str,list),'lastplayed': str,'album': str,'artist': list,'votes': str,'path': str,'trailer': str,'dateadded': str,'mediatype': str,'dbid': int}

#per channel rule limit
RULES_PER_PAGE                   = 10
#builder
RULES_ACTION_CHANNEL_CREATION    = 1 
RULES_ACTION_START               = 2
RULES_ACTION_CHANNEL_START       = 3
RULES_ACTION_CHANNEL_JSON        = 4
RULES_ACTION_CHANNEL_ITEM        = 5
RULES_ACTION_CHANNEL_LIST        = 6
RULES_ACTION_CHANNEL_STOP        = 7
RULES_ACTION_CHANNEL_PRE_TIME    = 8
RULES_ACTION_CHANNEL_POST_TIME   = 9
RULES_ACTION_STOP                = 10
#player
RULES_ACTION_PLAYBACK            = 11
RULES_ACTION_PLAYER              = 12
#overlay
RULES_ACTION_OVERLAY             = 20

#overlay globals
NOTIFICATION_CHECK_TIME          = 15.0 #seconds
NOTIFICATION_TIME_REMAINING      = 60 #seconds
NOTIFICATION_TIME_BEFORE_END     = 15 #seconds
NOTIFICATION_DISPLAY_TIME        = 30 #seconds
CHANNELBUG_CHECK_TIME            = 15.0 #seconds

# Actions
ACTION_PREVIOUS_MENU         = [9, 10, 92, 216, 247, 257, 275, 61467, 61448, 110]

USER_LOC         = (REAL_SETTINGS.getSetting('User_Folder') or SETTINGS_LOC)
XMLTVFLE         = os.path.join(USER_LOC ,'%s.xml'%('pseudotv'))
M3UFLE           = os.path.join(USER_LOC ,'%s.m3u'%('pseudotv'))
CHANNELFLE       = os.path.join(USER_LOC ,'channels.json')
LIBRARYFLE       = os.path.join(USER_LOC ,'library.json')
GENREFLE         = os.path.join(USER_LOC ,'genres.xml')
CACHE_LOC        = os.path.join(USER_LOC ,'cache')
LOCK_LOC         = USER_LOC
TEMP_LOC         = os.path.join(CACHE_LOC,'temp')
LOGO_LOC         = os.path.join(CACHE_LOC,'logos')
LOGO_COLOR_LOC   = os.path.join(LOGO_LOC ,'color')
LOGO_MONO_LOC    = os.path.join(LOGO_LOC ,'mono')
PLS_LOC          = os.path.join(CACHE_LOC,'playlists')

MGR_SETTINGS     = {'refresh_interval':'1',
                    'iptv_simple_restart':'false'}
                    
PVR_SETTINGS     = {'m3uRefreshMode':'1','m3uRefreshIntervalMins':'5','m3uRefreshHour':'0',
                    'logoPathType':'0','logoPath':LOGO_LOC,
                    'm3uPathType':'0','m3uPath':M3UFLE,
                    'epgPathType':'0','epgPath':XMLTVFLE,
                    'genresPathType':'0','genresPath':GENREFLE,
                    'useEpgGenreText':'true', 'logoFromEpg':'1',
                    'catchupEnabled':'true','allChannelsCatchupMode':'0',
                    'numberByOrder':'false','startNum':'1',
                    'epgTimeShift':'0','epgTSOverride':'false',
                    'useFFmpegReconnect':'true','useInputstreamAdaptiveforHls':'true'}
 
def log(msg, level=xbmc.LOGDEBUG):
    try: msg = str(msg)
    except: pass
    if not REAL_SETTINGS.getSetting('Enable_Debugging') == "true" and level != xbmc.LOGERROR: return
    if   level == xbmc.LOGERROR: msg = '%s, %s'%((msg),traceback.format_exc())
    try: xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg),level)
    except Exception as e: xbmc.log('log failed! %s'%(e),level)

def getProperty(key, id=10000):
    try: 
        key = '%s.%s'%(ADDON_ID,key)
        value = xbmcgui.Window(id).getProperty(key)
        if value: log("globals: getProperty, key = " + key + ", value = " + value)
        return value
    except Exception as e: log("globals: getProperty, Failed! " + str(e), xbmc.LOGERROR)
    return ''
    
def setProperty(key, value, id=10000):
    key = '%s.%s'%(ADDON_ID,key)
    if not isinstance(value, basestring): value = str(value)
    log("globals: setProperty, key = " + key + ", value = " + value)
    try: xbmcgui.Window(id).setProperty(key, value)
    except Exception as e: log("globals: setProperty, Failed! " + str(e), xbmc.LOGERROR)
    return True
    
def clearProperty(key, id=10000):
    key = '%s.%s'%(ADDON_ID,key)
    log("globals: clearProperty, key = %s"%(key))
    xbmcgui.Window(id).clearProperty(key)

def getPropertyBool(key):
    return getProperty(key).title() == 'True'
    
def setPropertyBool(key, value):
    return setProperty(key,str(value).title())

def isLegacyPseudoTV(): # legacy setting to disable/enable support in third-party applications. 
    return getPropertyBool('PseudoTVRunning')

def setLegacyPseudoTV(state):
    return setPropertyBool('PseudoTVRunning',state)

def setSetting(key,value):
    log('globals: setSetting, key = %s, value = %s'%(key,value))
    return REAL_SETTINGS.setSetting(key,value)

def getSetting(key, reload=True):
    if reload: REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
    value = REAL_SETTINGS.getSetting(key)
    log('globals: getSetting, key = %s, value = %s'%(key,value))
    return value
    
def getSettingBool(key, reload=True):
    if reload: REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
    try:
        return REAL_SETTINGS.getSettingBool(key)
    except:
        return getSetting(key) == "true" 
    
def getSettingInt(key, reload=True):
    if reload: REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
    try: 
        return REAL_SETTINGS.getSettingInt(key)
    except:
        value = getSetting(key)
        if value.isdecimal():
            return float(value)
        elif value.isdigit(): 
            return int(value)

def unquote(text):
    return urllib.parse.unquote(text)
    
def quote(text):
    return urllib.parse.quote(text)

PAGE_LIMIT       = getSettingInt('Page_Limit')
MIN_ENTRIES      = int(PAGE_LIMIT//2)
LOGO             = (COLOR_LOGO if bool(getSettingInt('Color_Logos')) else MONO_LOGO).replace(ADDON_PATH,'special://home/addons/%s/'%(ADDON_ID)).replace('\\','/')

@contextmanager
def fileLocker(GlobalFileLock):
    log('globals: fileLocker')
    GlobalFileLock.lockFile("MasterLock")
    try: yield
    finally: 
        GlobalFileLock.unlockFile('MasterLock')
        GlobalFileLock.close()

@contextmanager
def busy():
    log('globals: busy')
    if isBusy(): yield
    setBusy(True)
    try: yield
    finally: 
        setBusy(False)

@contextmanager
def busy_dialog(escape=False):
    if not escape:
        log('globals: busy_dialog')
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        try: yield
        finally: xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
    else: yield

def initDirs():
    dirs = [CACHE_LOC,LOGO_LOC,PLS_LOC,LOCK_LOC]
    [FileAccess.makedirs(dir) for dir in dirs if not FileAccess.exists(dir)]
    return True

def notificationDialog(message, header=ADDON_NAME, sound=False, time=4000, icon=COLOR_LOGO):
    log('globals: notificationDialog: ' + message)
    try: xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
    except Exception as e:
        log("globals: notificationDialog Failed! " + str(e), xbmc.LOGERROR)
        xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
    return True
     
def notificationProgress(message, header=ADDON_NAME, func=None, args=None, kwargs={}, time=4):
    dia = ProgressBGDialog(message=message,header=header)
    for i in range(time):
        # if func: func(*args, **kwargs)
        if MY_MONITOR.waitForAbort(1): break
        dia = ProgressBGDialog((((i + 1) * 100)//time),control=dia,header=header)
    return ProgressBGDialog(100,control=dia)
    
def okDialog(msg, heading=ADDON_NAME):
    return xbmcgui.Dialog().ok(heading, msg)
    
def textviewer(msg, heading=ADDON_NAME, usemono=False):
    return xbmcgui.Dialog().textviewer(heading, msg, usemono)
    
def yesnoDialog(message, heading=ADDON_NAME, nolabel='', yeslabel='', customlabel='', autoclose=0):
    try:    
        if customlabel:
            return xbmcgui.Dialog().yesnocustom(heading, message, customlabel, nolabel, yeslabel, autoclose)
        else: raise Exception()
    except: return xbmcgui.Dialog().yesno(heading, message, nolabel, yeslabel, autoclose)
    
def browseDialog(type=0, heading=ADDON_NAME, default='', shares='', mask='', options=None, useThumbs=True, treatAsFolder=False, prompt=True, multi=False, monitor=False):
    if prompt and not default:
        if options is None:
            options  = [{"label":"Video Playlists" , "label2":"Video Playlists"               , "default":"special://profile/playlists/video/" , "mask":'.xsp'     , "type":1, "multi":False},
                        {"label":"Music Playlists" , "label2":"Music Playlists"               , "default":"special://profile/playlists/music/" , "mask":'.xsp'     , "type":1, "multi":False},
                        {"label":"Video"           , "label2":"Video Sources"                 , "default":"library://video/"                   , "mask":VIDEO_EXTS , "type":0, "multi":False},
                        {"label":"Music"           , "label2":"Music Sources"                 , "default":"library://music/"                   , "mask":MUSIC_EXTS , "type":0, "multi":False},
                        {"label":"Pictures"        , "label2":"Picture Sources"               , "default":""                                   , "mask":IMAGE_EXTS , "type":0, "multi":False},
                        {"label":"Files"           , "label2":"File Sources"                  , "default":""                                   , "mask":""         , "type":0, "multi":False},
                        {"label":"Local"           , "label2":"Local Drives"                  , "default":""                                   , "mask":""         , "type":0, "multi":False},
                        {"label":"Network"         , "label2":"Local Drives and Network Share", "default":""                                   , "mask":""         , "type":0, "multi":False},
                        {"label":"Resources"       , "label2":"Resource Plugins"              , "default":"resource://"                        , "mask":""         , "type":0, "multi":False}]
        listitems = [buildMenuListItem(option['label'],option['label2'],iconImage=COLOR_LOGO) for option in options]

        select    = selectDialog(listitems, LANGUAGE(30116), multi=False)
        if select is not None:
            shares    = options[select]['label'].lower().replace("network","")
            mask      = options[select]['mask']
            type      = options[select]['type']
            multi     = options[select]['multi']
            default   = options[select]['default']
    log('globals: browseDialog, type = %s, heading= %s, shares= %s, mask= %s, useThumbs= %s, treatAsFolder= %s, default= %s'%(type, heading, shares, mask, useThumbs, treatAsFolder, default))
    if monitor: toggleCHKInfo(True)
    if multi == True:
        # https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html#ga856f475ecd92b1afa37357deabe4b9e4
        # type integer - the type of browse dialog.
        # 1	ShowAndGetFile
        # 2	ShowAndGetImage
        retval = xbmcgui.Dialog().browseMultiple(type, heading, shares, mask, useThumbs, treatAsFolder, default)
    else:
        # https://codedocs.xyz/xbmc/xbmc/group__python___dialog.html#gafa1e339e5a98ae4ea4e3d3bb3e1d028c
        # type integer - the type of browse dialog.
        # 0	ShowAndGetDirectory
        # 1	ShowAndGetFile
        # 2	ShowAndGetImage
        # 3	ShowAndGetWriteableDirectory
        retval = xbmcgui.Dialog().browseSingle(type, heading, shares, mask, useThumbs, treatAsFolder, default)
    if monitor: toggleCHKInfo(False)
    if retval:
        if prompt and retval == default: return None
        return retval
    return None
      
def inputDialog(message, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    # Types:
    # - xbmcgui.INPUT_ALPHANUM (standard keyboard)
    # - xbmcgui.INPUT_NUMERIC (format: #)
    # - xbmcgui.INPUT_DATE (format: DD/MM/YYYY)
    # - xbmcgui.INPUT_TIME (format: HH:MM)
    # - xbmcgui.INPUT_IPADDRESS (format: #.#.#.#)
    # - xbmcgui.INPUT_PASSWORD (return md5 hash of input, input is masked)
    retval = xbmcgui.Dialog().input(message, default, key, opt, close)
    if retval: return retval
    return None
    
def selectDialog(list, header=ADDON_NAME, preselect=None, useDetails=True, autoclose=0, multi=True):
    if multi == True:
        if preselect is None: preselect = []
        select = xbmcgui.Dialog().multiselect(header, list, autoclose, preselect, useDetails)
    else:
        if preselect is None:  preselect = -1
        select = xbmcgui.Dialog().select(header, list, autoclose, preselect, useDetails)
    if select is not None: return select
    return None

def ProgressBGDialog(percent=0, control=None, message='', header=ADDON_NAME):
    if (getSettingBool('Silent_OnPlayback') & isOverlay() & xbmc.getCondVisibility('Player.Playing')):
        if control is None: return
        else: return control.close()
    if control is None and percent == 0:
        control = xbmcgui.DialogProgressBG()
        control.create(header, message)
    elif control:
        if percent == 100 or control.isFinished(): return control.close()
        else: control.update(percent, header, message)
    return control

def getIdleTime():
    try: return (int(xbmc.getGlobalIdleTime()) or 0)
    except: return 0 #Kodi raises error after sleep.
    
def hasPVR():
    return xbmc.getCondVisibility('Pvr.HasTVChannels')
    
def hasMusic():
    return xbmc.getCondVisibility('Library.HasContent(Music)')
    
def hasTV():
    return xbmc.getCondVisibility('Library.HasContent(TVShows)')
    
def hasMovie():
    return xbmc.getCondVisibility('Library.HasContent(Movies)')

def setBusy(state):
    return setProperty("BUSY.RUNNING",str(state))
    
def isBusy():
    return (getProperty("BUSY.RUNNING") == "True")

def isOverlay():
    return getPropertyBool('OVERLAY')

def padLST(lst, targetLen):
    if len(lst) == 0: return lst
    lst.extend(list([random.choice(lst) for n in range(targetLen - len(lst))]))
    return lst[:targetLen]
    
def chkVersion(cleanStart=False):
    lastVersion = (getSetting('lastVersion') or 'v.0.0.0')
    if ADDON_VERSION != lastVersion:
        setSetting('lastVersion',ADDON_VERSION)
        return showChangelog()
        # if cleanStart:
            # xbmc.executebuiltin('RunPlugin("(plugin://'+ADDON_ID+'/?channel&mode=Utilities&name=Clean%20Start%2c%20Delete%20all%20files%20and%20settings.&url)")')
    return False
    
def showChangelog():
    changelog = xbmcvfs.File(CHANGELOG_FLE).read().replace('-Added','[B][COLOR=green]-Added:[/COLOR][/B]').replace('-Important','[B][COLOR=red]-Important:[/COLOR][/B]').replace('-Notice','[B][COLOR=orange]-Notice:[/COLOR][/B]').replace('-Warning','[B][COLOR=red]-Warning:[/COLOR][/B]').replace('-Removed','[B][COLOR=red]-Removed:[/COLOR][/B]').replace('-Fixed','[B][COLOR=orange]-Fixed:[/COLOR][/B]').replace('-Improved','[B][COLOR=yellow]-Improved:[/COLOR][/B]').replace('-Tweaked','[B][COLOR=yellow]-Tweaked:[/COLOR][/B]').replace('-Changed','[B][COLOR=yellow]-Changed:[/COLOR][/B]')
    return textviewer(changelog,heading=(LANGUAGE(30134)%(ADDON_NAME,ADDON_VERSION)),usemono=True)

def dumpJSON(dict1, idnt=None, sortkey=True):
    if not dict1: return ''
    elif isinstance(dict1, basestring): return dict1
    return (json.dumps(dict1, indent=idnt, sort_keys=sortkey))
    
def loadJSON(item):
    if isinstance(item,dict):
        log("globals: loadJSON item already mutable")
        return item
    elif isinstance(item,basestring):
        try: return json.loads(item, strict=False)
        except Exception as e: log("globals: loadJSON failed! %s\n%s"%(e,item), xbmc.LOGERROR)
    return {}
    
def sendJSON(command):
    response = loadJSON(xbmc.executeJSONRPC(command))
    log('globals: sendJSON, command = %s, response = %s'%(command, response))
    return response

def getSeason():
    try: return {'September':'startrek','October':'horror','December':'xmas','May':'starwars'}[datetime.datetime.now().strftime('%B')]
    except: return 'none'
        
def buildMenuListItem(label1="", label2="", iconImage=None, url="", infoItem=None, artItem=None, propItem=None, oscreen=True, mType='video'):
    listitem  = xbmcgui.ListItem(label1, label2, path=url, offscreen=oscreen)
    iconImage = (iconImage or COLOR_LOGO)
    if propItem: listitem.setProperties(propItem)
    if infoItem: listitem.setInfo(mType, infoItem)
    else: listitem.setInfo(mType,   {'mediatype': 'video',
                                     'Label' : label1,
                                     'Label2': label2,
                                     'Title' : label1})
    if artItem: listitem.setArt(artItem)
    else: listitem.setArt({'thumb': iconImage,
                           'icon' : iconImage})
    return listitem

def splitall(plugin):
    plugin = [plugin]
    while not MY_MONITOR.abortRequested():
        last   = plugin
        plugin = os.path.split(plugin[0])
        if not plugin[0]: break
    return last[0]
    
def getPluginMeta(plugin):
    log('globals: plugin = %s'%(plugin))
    try:
        if plugin.startswith(('plugin://','resource://')): plugin = splitall(plugin)
        pluginID = xbmcaddon.Addon(plugin.strip())
        return {'type':pluginID.getAddonInfo('type'),'label':pluginID.getAddonInfo('name'),'name':pluginID.getAddonInfo('name'), 'version':pluginID.getAddonInfo('version'), 'path':pluginID.getAddonInfo('path'), 'author':pluginID.getAddonInfo('author'), 'icon':pluginID.getAddonInfo('icon'), 'fanart':pluginID.getAddonInfo('fanart'), 'id':pluginID.getAddonInfo('id'), 'description':(pluginID.getAddonInfo('description') or pluginID.getAddonInfo('summary'))}
    except Exception as e: log("globals, Failed! %s"%(e), xbmc.LOGERROR)
    return {}
        
def togglePVR(state='true'):
    return sendJSON('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"%s","enabled":%s}, "id": 1}'%(PVR_CLIENT,state))

def brutePVR(override=False):
    if (xbmc.getCondVisibility("Pvr.IsPlayingTv") or xbmc.getCondVisibility("Player.HasMedia")): 
        return
    elif not override:
        if not yesnoDialog('%s ?'%(LANGUAGE(30065)%(getPluginMeta(PVR_CLIENT).get('name','')))): return
    togglePVR('false')
    xbmc.sleep(2000)
    togglePVR('true')
    if override: return True
    return notificationDialog(LANGUAGE(30053))

def getPVR(id=PVR_CLIENT):
    try: return xbmcaddon.Addon(id)
    except: # backend disabled?
        togglePVR('true')
        xbmc.sleep(1000)
        try:
            return xbmcaddon.Addon(id)
        except: return None

def chkMGR():
    return chkPVR(PVR_MANAGER, MGR_SETTINGS)

def chkPVR(id=PVR_CLIENT, values=PVR_SETTINGS):
    log('globals: chkPVR, id = %s'%(id))
    #check for min. settings' required
    addon = getPVR(id)
    if addon is None: return False
    for setting, value in values.items():
        if not str(addon.getSetting(setting)) == str(value): 
            return configurePVR(id,values,getSettingBool('Enable_Config'))
    return True
    
def configurePVR(id=PVR_CLIENT,values=PVR_SETTINGS,override=False):
    log('globals: configurePVR')
    if not override:
        if not yesnoDialog('%s ?'%(LANGUAGE(30012)%(getPluginMeta(id).get('name',''),ADDON_NAME,))): return
    try:
        addon = getPVR(id)
        if addon is None: return False
        for setting, value in values.items(): 
            addon.setSetting(setting, value)
    except: return notificationDialog(LANGUAGE(30049)%(id))
    if override: return True
    return notificationDialog(LANGUAGE(30053))

def refreshMGR():
    if getPVR(PVR_MANAGER):
        xbmc.executebuiltin('RunScript(service.iptv.manager,refresh)')

def strpTime(datestring, format='%Y-%m-%d %H:%M:%S'):
    try: return datetime.datetime.strptime(datestring, format)
    except TypeError: return datetime.datetime.fromtimestamp(time.mktime(time.strptime(datestring, format)))

def getLocalTime():
    offset = (datetime.datetime.utcnow() - datetime.datetime.now())
    return time.time() + offset.total_seconds()

def getDeltaTime(time):
    datetime.datetime.fromtimestamp(time) + datetime.timedelta(time)

def escapeDirJSON(path):
    mydir = path
    if (mydir.find(":")): mydir = mydir.replace("\\", "\\\\")
    return mydir
        
def buildItemListItem(item, mType='video', oscreen=True, playable=True):
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
           
def isHD(item):
    if 'isHD' in item: return item['isHD']
    elif 'streamdetails' in item: 
        item = item.get('streamdetails',{})
        if 'video' in item and len(item.get('video')) > 0:
            videowidth  = int(item['video'][0]['width']  or '0')
            videoheight = int(item['video'][0]['height'] or '0')
            if videowidth >= 1280 and videoheight >= 720: return True  
    return False

def is3D(item):
    if 'is3D' in item: return item['is3D']
    if 'streamdetails' in item: item = item.get('streamdetails',{})
    if 'video' in item and item.get('video') != [] and len(item.get('video')) > 0:
        stereomode = (item['video'][0]['stereomode'] or '')
        if len(stereomode) > 0: return True
    return False
        
def splitYear(label):
    match = re.compile('(.*) \((.*)\)', re.IGNORECASE).search(label)
    if match:
        if match.group(2): return match.groups()
    return label, None
        
def getLabel(item):
    label = (item.get('name','') or item.get('label','') or item.get('showtitle','') or item.get('title',''))
    if not label: return ''
    label, year = splitYear(label)
    year = (item.get('year','') or year)
    if year: return '%s (%s)'%(label, year)
    return label
    
def getThumb(item,opt=0): #unify thumbnail artwork
    keys = {0:['landscape','fanart','poster','thumb','thumbnail','folder','icon'],
            1:['poster','landscape','fanart','thumb','thumbnail','folder','icon']}[opt]
    for key in keys:
        art = (item.get('art',{}).get('season.%s'%(key),'') or 
               item.get('art',{}).get('tvshow.%s'%(key),'') or 
               item.get('art',{}).get(key,'')               or
               item.get(key,''))
        if art: return art
    return LOGO

def funcExecute(func,args):
    log("globals: funcExecute, func = %s, args = %s"%(func.__name__,args))
    if isinstance(args,dict): 
        retval = func(**args)
    elif isinstance(args,tuple): 
        retval = func(*args)
    elif args:
        retval = func(args)
    else: 
        retval = func()
    log("globals: funcExecute, retval = %s"%(retval))
    return retval

def assertLST(lst1,lst2): #test if both lists match. 
    assertBool = len(diffLST(lst1,lst2)) == 0
    log('globals: assertLST = %s'%(assertBool))
    return assertBool
    
def diffLST(lst1, lst2): 
    difference = (list(set(lst1) - set(lst2)))
    log('globals: diffLST = %s'%(difference))
    return difference
    
def assertDICT(dict1,dict2,return_diff=False): #test if both dicts match.
    difference = diffDICT(dict1,dict2)
    assertBool = len(difference) == 0
    log('globals: assertDICT = %s'%(assertBool))
    if return_diff: return assertBool, difference
    return assertBool
    
def diffDICT(dict1, dict2): 
    intersec = [item for item in dict1 if item in dict2]
    difference = [item for item in chain(dict1,dict2) if item not in intersec]
    log('globals: diffDICT = %s'%(dumpJSON(difference)))
    return difference
    
def mergeDICT(dict1, dict2):
    return [{**u, **v} for u, v in zip_longest(dict1, dict2, fillvalue={})]

def removeDupsDICT(list):
    return [dict(tupleized) for tupleized in set(tuple(item.items()) for item in list)]

def removeDUPSLST(lst):
    list_of_strings = [dumpJSON(d) for d in lst]
    list_of_strings = set(list_of_strings)
    return [loadJSON(s) for s in list_of_strings]

def cleanLabel(text):
    text = re.sub('\[COLOR=(.+?)\]', '', text)
    text = re.sub('\[/COLOR\]', '', text)
    text = text.replace("[B]",'').replace("[/B]",'')
    text = text.replace("[I]",'').replace("[/I]",'')
    return text.replace(":",'')

def hasPVRitem():
    pvritem = len(getCurrentChannelItem()) > 0
    log('globals: hasPVRitem = %s'%(pvritem))
    return pvritem
    
def isPseudoTV():
    isPseudoTV = hasChannelData('VideoPlayer') #condition set only while playing
    log('globals: isPseudoTV = %s'%(isPseudoTV))
    return isPseudoTV

def getWriter(text):
    if isinstance(text, basestring):
        writer = re.search(r'\[COLOR item=\"(.+?)\"]\[/COLOR]', text)
        if writer: return loadJSON(decodeString(writer.group(1)))
    return {}

def getWriterfromString(type='ListItem'):
    return getWriter(xbmc.getInfoLabel('%s.Writer'%(type)))
    
def hasChannelData(type='ListItem'):
    return getWriterfromString(type).get('citem',{}).get('number',-1) > 0
  
def setCurrentChannelItem(item):
    setProperty('channel_item',dumpJSON(item))
    
def getCurrentChannelItem():
    return loadJSON(getProperty('channel_item'))
  
def clearCurrentChannelItem():
    clearProperty('channel_item')
  
def getChannelID(name, path, number):
    if isinstance(path, list): path = '|'.join(path)
    tmpid = '%s.%s.%s'%(number, name, hashlib.md5(path.encode(DEFAULT_ENCODING)))
    return '%s@%s'%((binascii.hexlify(tmpid.encode(DEFAULT_ENCODING))[:32]).decode(DEFAULT_ENCODING),slugify(ADDON_NAME))

def encodeString(text):
    base64_bytes = base64.b64encode(text.encode(DEFAULT_ENCODING))
    return base64_bytes.decode(DEFAULT_ENCODING)

def decodeString(base64_bytes):
    message_bytes = base64.b64decode(base64_bytes.encode(DEFAULT_ENCODING))
    return message_bytes.decode(DEFAULT_ENCODING)

def getGroups():
    if getSetting('User_Groups'): GROUP_TYPES.extend(getSetting('User_Groups').split('|'))
    return sorted(set(GROUP_TYPES))

def genUUID(seed=None):
    if seed:
        m = hashlib.md5()
        m.update(seed.encode(DEFAULT_ENCODING))
        return str(uuid.UUID(m.hexdigest()))
    return str(uuid.uuid1(clock_seq=CLOCK_SEQ))

def getIP():
    return (xbmc.getIPAddress() or None)

def setMYUUID():
    uuid = genUUID(seed=getIP())
    setSetting('MY_UUID',uuid)
    return uuid
    
def getMYUUID():
    uuid = getSetting('MY_UUID')
    if not uuid: return setMYUUID()
    return uuid
        
def getClient():
    return getSettingBool('Enable_Client')
    
def setClient(state):
    return setSetting('Enable_Client',state)
        
def slugify(text):
    non_url_safe = [' ','"', '#', '$', '%', '&', '+',',', '/', ':', ';', '=', '?','@', '[', '\\', ']', '^', '`','{', '|', '}', '~', "'"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text

def saveURL(url, file):
    try:
        contents = urllib.request.urlopen(url).read()
        fle = FileAccess.open(file, 'w')
        fle.write(contents)
        fle.close()
    except Exception as e: 
        log("saveURL, Failed! %s"%e, xbmc.LOGERROR)
    
def interleave(*args): #interleave multi-lists, while preserving order
    try:
        iters = list(map(iter, args))
        while iters and not MY_MONITOR.abortRequested():
            it = random.choice(iters)
            try: yield next(it)
            except StopIteration:
                iters.remove(it)
    except Exception as e: 
        log("interleave, Failed! %s"%(e), xbmc.LOGERROR)
        yield list(chain.from_iterable(izip_longest(*args)))[0]

def isStack(path,file=None):
    if file is not None: 
        return path.startswith('stack://%s'%(file))
    else:
        return path.startswith('stack://')

def hasStack(path,file=None):
    if isStack(path,file): return splitStacks(path)
    return None

def splitStacks(path): #split stack for indv. files.
    log('splitStacks, path = %s'%(path))
    return (path.split('stack://')[1]).split(' , ')
                                      
def stripStack(path, file): #strip pre-rolls from stack, return file.
    log('stripStack, path = %s, file = %s'%(path,file))
    paths = path.split(' , ')
    for idx, path in enumerate(paths.copy()):
        if not path == file: paths.pop(idx)
        elif path == file: break
    return paths
    
def buildStack(paths):
    stack = 'stack://%s'
    return stack%(' , '.join(paths))
    
def cleanMPAA(mpaa):
    mpaa = mpaa.lower()
    if ':' in mpaa: mpaa = re.split(':',mpaa)[1]  #todo prop. regex
    if 'rated ' in mpaa: mpaa = re.split('rated ',mpaa)[1]  #todo prop. regex
    return mpaa.upper()
        
def cleanResourcePath(path):
    if path.startswith('resource://'):
        return (path.replace('resource://','special://home/addons/'))
    return path
    
def percentDiff(org, new):
    try: return (abs(float(org) - float(new)) / float(new)) * 100.0
    except ZeroDivisionError: return 0
        
def fillInfoMonitor(type='ListItem'):
    item = {'name'  :xbmc.getInfoLabel('%s.Label'%(type)),
            'label' :xbmc.getInfoLabel('%s.Label'%(type)),
            'label2':xbmc.getInfoLabel('%s.Label2'%(type)),
            'path'  :xbmc.getInfoLabel('%s.Path'%(type)),
            'writer':xbmc.getInfoLabel('%s.Writer'%(type)),
            'logo'  :xbmc.getInfoLabel('%s.Icon'%(type)),
            'thumb' :xbmc.getInfoLabel('%s.Thumb'%(type))}    
    montiorList = list(filter(lambda k:k != '', getInfoMonitor()))
    infoItem = dumpJSON(item)
    if infoItem:
        montiorList.insert(0,infoItem)
        setProperty('monitor.montiorList' ,'|'.join(list(set(montiorList))))
    return True
    
def getInfoMonitor():
    return getProperty('monitor.montiorList').split('|')

def toggleCHKInfo(state):
    setProperty('chkInfo',str(state))
    if state: clearProperty('monitor.montiorList')
    else: clearProperty('chkInfo')
    
def isCHKInfo():
    return getProperty('chkInfo') == "True"
        
def hasSubtitle():
    return xbmc.getCondVisibility('VideoPlayer.HasSubtitles')

def isSubtitle():
    return xbmc.getCondVisibility('VideoPlayer.SubtitlesEnabled')
    
def installAddon(id):
    if xbmc.getCondVisibility('System.HasAddon("%s")'%(id)) == 1: return False
    xbmc.executebuiltin('InstallAddon("%s")'%(id))
    return notificationDialog('%s %s...'%(LANGUAGE(30193),id))
        
def getRandomPage(limit,total=50):
    page = random.randrange(0, total, limit)
    log('globals: getRandomPage, page = %s'%(page))
    return page, page+limit

def isPlaylistRandom():
    return xbmc.getInfoLabel('Playlist.Random').lower() == 'on' # Disable auto playlist shuffling if it's on
    
def isPlaylistRepeat():
    return xbmc.getInfoLabel('Playlist.IsRepeat').lower() == 'true' # Disable auto playlist repeat if it's on #todo

def findItemsIn(items, values, item_key='getLabel', val_key='', index=True):
    log("globals: findItemsIn, values = %s, item_key = %s, val_key = %s, index = %s"%(values, item_key, val_key, index))
    matches = []
    def match(fkey,fvalue):
        if fkey.lower() == fvalue.lower():
            matches.append(idx if index else item)
        
    if not values: return [-1]
    for idx, item in enumerate(items):
        for value in values:
            if isinstance(value,dict): 
                value = value.get(val_key,'')
                
            if isinstance(item,xbmcgui.ListItem): 
                if item_key == 'getLabel':  
                    match(item.getLabel() ,value)
                elif item_key == 'getLabel2': 
                    match(item.getLabel2(),value)
            elif isinstance(item,dict):       
                match(item.get(item_key,''),value)
            else:                             
                match(item,value)
    log("globals: findItemsIn, matches = %s"%(matches))
    return matches

def titleLabels(list):
     return [str(item).title() for item in list]
 
def roundTimeDown(thetime, offset=30): # round the given time down to the nearest
    n = datetime.datetime.fromtimestamp(thetime)
    delta = datetime.timedelta(minutes=offset)
    if n.minute < (offset): n = n.replace(minute=0, second=0, microsecond=0)
    else: n = n.replace(minute=offset, second=0, microsecond=0)
    return time.mktime(n.timetuple())
    
def roundTimeUp(thetime, offset=30): # round the given time up to the nearest
    n = datetime.datetime.fromtimestamp(thetime)
    delta = datetime.timedelta(minutes=offset)
    n = (n + (datetime.datetime.min - n) % delta)
    return time.mktime(n.timetuple())
    
def pagination(list, end):
    for start in xrange(0, len(list), end):
        yield seq[start:start+end]

def getChannelSuffix(name, type):
    if name.endswith((LANGUAGE(30155),LANGUAGE(30157),LANGUAGE(30156),LANGUAGE(30177))): return name  
    elif type == LANGUAGE(30004): suffix = LANGUAGE(30155) #TV
    elif type == LANGUAGE(30097): suffix = LANGUAGE(30157) #Music
    elif type == LANGUAGE(30005): suffix = LANGUAGE(30156) #Movies
    else: return name
    return '%s %s'%(name,suffix)
 
def cleanChannelSuffix(name, type):
    if   type == LANGUAGE(30004): name = name.split(' %s'%LANGUAGE(30155))[0]#TV
    elif type == LANGUAGE(30097): name = name.split(' %s'%LANGUAGE(30157))[0]#Music
    elif type == LANGUAGE(30005): name = name.split(' %s'%LANGUAGE(30156))[0]#Movie
    return name

class PoolHelper:
    def __init__(self):
        if ENABLE_POOL: 
            self.pool = ThreadPool(THREAD_CORES)
            log("PoolHelper: CPU CORES = " + str(THREAD_CORES))
        else: log("PoolHelper: ThreadPool Disabled")
        

    def runSelf(self, func):
        return func()
        
        
    def poolList(self, method, items=None, args=None, chunk=1):
        log("PoolHelper: poolList")
        results = []
        if ENABLE_POOL:
            if items is None and args is None: 
                results = self.pool.map(self.runSelf, method, chunksize=chunk)
            elif args is not None: 
                results = self.pool.map(method, zip(items,repeat(args)), chunksize=chunk)
            elif items: 
                results = self.pool.map(method, items, chunksize=chunk)
            self.pool.close()   
            self.pool.join()
        else:
            if items is None and args is None: 
                results = [self.runSelf(func) for func in method]
            elif args is not None: 
                results = [method((item, args)) for item in items]
            elif items: 
                results = [method(item) for item in items]
        return list(filter(None, results))