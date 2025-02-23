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
# https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#m3u-format-elements
# https://raw.githubusercontent.com/XMLTV/xmltv/master/xmltv.dtd
# -*- coding: utf-8 -*-

from resources.lib.globals     import *
from resources.lib             import xmltv
from resources.lib.vault       import Vault
from resources.lib.channels    import Channels
from resources.lib.library     import Library

class Writer:
    GlobalFileLock = FileLock()

    def __init__(self, inherited=None):
        self.log('__init__')
        if inherited:
            self.monitor      = inherited.monitor
            self.player       = inherited.player
            self.cache        = inherited.cache
            self.dialog       = inherited.dialog
            self.pool         = inherited.pool
            self.rules        = inherited.rules
        else:
            from resources.lib.cache       import Cache
            from resources.lib.concurrency import PoolHelper
            from resources.lib.rules       import RulesList
            self.monitor      = xbmc.Monitor()
            self.player       = xbmc.Player()
            self.cache        = Cache()
            self.dialog       = Dialog()
            self.pool         = PoolHelper()
            self.rules        = RulesList()
        
        if not inherited.__class__.__name__ in ['Builder','Config']:
            self.progDialog   = None
            self.progress     = None
            self.chanName     = None
        else:
            self.progDialog   = inherited.progDialog
            self.progress     = inherited.progress
            self.chanName     = inherited.chanName
            
        if not inherited.__class__.__name__ == 'JSONRPC':
            from resources.lib.jsonrpc import JSONRPC 
            self.jsonRPC      = JSONRPC(self)
        else:
            self.jsonRPC      = inherited
        
        self.vault            = Vault()   
        self.m3u              = M3U(writer=self)
        self.xmltv            = XMLTV(writer=self)
        self.channels         = Channels(writer=self)
        self.library          = Library(writer=self)
        self.recommended      = self.library.recommended
      
      
    def log(self, msg, level=xbmc.LOGDEBUG):
        return log('%s: %s'%(self.__class__.__name__,msg),level)
    
        
    def isClient(self):
        client = self.channels.isClient
        PROPERTIES.setPropertyBool('isClient',client)
        return client
              
              
    def getEndtime(self, id, fallback):
        # if self.xmltv.reload():
        endtime = (self.xmltv.getEndtimes().get(id,'') or fallback)
        self.log('getEndtime, id = %s, endtime = %s, fallback = %s'%(id,endtime,fallback))
        return endtime


    def delete(self, full=False):
        self.log('delete')
        funcs = [self.m3u.delete,
                 self.xmltv.delete]
        if full: funcs.append(self.channels.delete)
        if False in [func() for func in funcs]:
            return False
        if full: setRestartRequired(True)
        return True
        
        
    def saveChannels(self):
        self.log('saveChannels')
        SETTINGS.setSetting('Select_Channels','[B]%s[/B] Channels'%(len(self.channels.getChannels())))
        return self.channels.save()
        
        
    def save(self, exImport=True):
        self.log('save')
        funcs = [self.m3u,
                 self.xmltv]
        if self.cleanChannels():
            if exImport: self.importSETS()
            if False in [func.save() for func in funcs]:
                self.dialog.notificationDialog(LANGUAGE(30001))
                return False
            else:
                if self.progDialog is not None:
                    self.progDialog = self.dialog.progressBGDialog(self.progress, self.progDialog, message=LANGUAGE(30152))
                return True
        

    def importSETS(self):
        self.log('importSETS')
        importLST = self.channels.getImports()
        if SETTINGS.getSettingBool('User_Import'):
            SETTINGS.setSetting('Import_M3U'  ,{0:SETTINGS.getSetting('Import_M3U_FILE')  ,1:SETTINGS.getSetting('Import_M3U_URL')}[SETTINGS.getSettingInt('Import_M3U_TYPE')])
            SETTINGS.setSetting('Import_XMLTV',{0:SETTINGS.getSetting('Import_XMLTV_FILE'),1:SETTINGS.getSetting('Import_XMLTV_URL')}[SETTINGS.getSettingInt('Import_XMLTV_TYPE')])
            importLST.append({'type':'iptv','name':'User M3U/XMLTV','m3u':{'path':SETTINGS.getSetting('Import_M3U'),'slug':SETTINGS.getSetting('Import_SLUG')},'xmltv':{'path':SETTINGS.getSetting('Import_XMLTV')}})
        for idx, importItem in enumerate(importLST):
            try:
                if importItem.get('type','') == 'iptv':
                    if self.progDialog is not None:
                        self.progDialog = self.dialog.progressBGDialog(self.progress, self.progDialog, message='%s'%(importItem.get('name','')),header='%s, %s'%(ADDON_NAME,LANGUAGE(30151)))
                    idx += 1
                    slug   = importItem.get('m3u'  ,{}).get('slug','')
                    m3ufle = importItem.get('m3u'  ,{}).get('path','')
                    xmlfle = importItem.get('xmltv',{}).get('path','')
                    self.m3u.importM3U(m3ufle,slug,multiplier=idx)
                    self.xmltv.importXMLTV(xmlfle,slug)
            except Exception as e: self.log(" importSETS, Failed! " + str(e), xbmc.LOGERROR)
        return True
        
        
    def addChannelLineup(self, citem, radio=False, catchup=True):
        item = citem.copy()
        item['label'] = (item.get('label','') or item['name'])
        item['url']   = 'plugin://%s/?mode=play&name=%s&id=%s&radio=%s'%(ADDON_ID,urllib.parse.quote(item['name']),urllib.parse.quote(item['id']),str(item['radio']))
        if not SETTINGS.getSettingBool('Enable_Grouping'): 
            item['group'] = [ADDON_NAME]
        else:
            item['group'].append(ADDON_NAME)
        item['group'] = list(set(item['group']))
        self.log('addChannelLineup, item = %s, radio = %s, catchup = %s'%(item,radio,catchup))
        self.m3u.addChannel(item)
        self.xmltv.addChannel(item)
    
    
    def removeChannel(self, citem): #remove channel completely from channels.json and m3u/xmltv
        self.log('removeChannel, citem = %s'%(citem))
        self.channels.remove(citem)
        self.removeChannelLineup(citem)
        
        
    def removeChannelLineup(self, citem): #clean channel from m3u/xmltv
        self.log('removeChannelLineup, citem = %s'%(citem))
        self.m3u.removeChannel(citem.get('id',''))
        self.xmltv.removeChannel(citem.get('id',''))
    

    def addProgrammes(self, citem, fileList, radio=False, catchup=True):
        self.log('addProgrammes, radio = %s, catchup = %s, programmes = %s, citem = %s'%(radio,catchup,len(fileList),citem))
        for idx, file in enumerate(fileList):
            item = {}
            item['radio']       = radio
            item['channel']     = citem['id']
            item['start']       = file['start']
            item['stop']        = file['stop']
            item['title']       = file['label']
            item['desc']        = file['plot']
            item['length']      = file['duration']
            item['sub-title']   = (file.get('episodetitle','') or '')
            item['rating']      = cleanMPAA(file.get('mpaa','')or 'NA')
            item['stars']       = (file.get('rating','')       or '0')
            item['categories']  = (file.get('genre','')        or ['Undefined'])
            item['type']        = file.get('type','video')
            item['new']         = int(file.get('playcount','1')) == 0
            item['thumb']       = getThumb(file,SETTINGS.getSettingInt('EPG_Artwork'))
            file['art']['thumb']= getThumb(file,{0:1,1:0}[SETTINGS.getSettingInt('EPG_Artwork')]) #unify thumbnail artwork, opposite of EPG_Artwork
            item['date']        = file.get('premiered','')
            
            if catchup:
                item['catchup-id'] = 'plugin://%s/?mode=vod&name=%s&id=%s&channel=%s&radio=%s'%(ADDON_ID,urllib.parse.quote(item['title']),urllib.parse.quote(encodeString((file.get('originalfile','') or file.get('file','')))),urllib.parse.quote(citem['id']),str(item['radio']))
            
            if (item['type'] != 'movie' and (file.get("episode",0) > 0)):
                item['episode-num'] = 'S%sE%s'%(str(file.get("season",0)).zfill(2),str(file.get("episode",0)).zfill(2))
                
            item['director']    = (','.join(file.get('director',[])))
            item['writer']      = (','.join(file.get('writer',[])))
            
            file['citem']       = citem #channel dict (stale data due to xmltv storage)
            item['fitem']       = file # kodi fileitem/listitem dict.
            
            # streamdetails       = file.get('streamdetails',{})
            # if streamdetails:
                # item['subtitle'] = list(set([sub.get('language','') for sub in streamdetails.get('subtitle',[]) if sub.get('language','')]))
                # item['audio']    = list(set([aud.get('codec','') for aud in streamdetails.get('audio',[]) if aud.get('codec','')]))
                # item['language'] = list(set([aud.get('language','') for aud in streamdetails.get('audio',[]) if aud.get('language','')]))
                # item['video']    = list(set([vid.get('aspect','') for vid in streamdetails.get('video',[]) if vid.get('aspect','')]))
            
            self.xmltv.addProgram(citem['id'], item)
            
            
    def clearChannels(self, all=False):
        channels = self.channels.getChannels()
        if not all: channels = list(filter(lambda citem:citem.get('number') <= CHANNEL_LIMIT, channels))
        self.log('cleanChannels, channels = %s'%(len(channels)))
        for citem in channels: 
            self.removeChannel(citem)
        if self.saveChannels():
            self.save()
        
            
    def cleanChannels(self): # remove abandoned/missing channels from m3u/xmltv
        self.log('cleanChannels')
        channels = self.channels.getChannels()
        m3u      = self.m3u.getChannels().copy()
        xmltv    = self.xmltv.getChannels().copy()
        
        for channel in channels:
            chid = channel.get('id','')
            if not chid: continue
            
            for idx, item in enumerate(m3u):
                if chid == item.get('id',''):
                    m3u.pop(idx)
                    
            for idx, item in enumerate(xmltv):
                if chid == item.get('id',''):
                    xmltv.pop(idx)
        
        for item in m3u:
            self.m3u.removeChannel(item.get('id',''))

        for item in xmltv: 
            self.xmltv.removeChannel(item.get('id',''))
        return True
        
    
    def recoverChannelsFromM3U(self):
        self.log('recoverChannelsFromM3U') #rebuild channels.json from m3u.
        channels = self.channels.getChannels()
        m3u      = self.m3u.getChannels().copy()
        if not channels and m3u:
            self.log('recoverChannelsFromM3U, recovering %s m3u channels'%(m3u))
            if not self.dialog.yesnoDialog('%s ?'%(LANGUAGE(30178))): return
            for item in m3u: 
                citem = self.channels.getCitem()
                citem.update(item) #todo repair path.
                self.channels.add(citem)
            return self.saveChannels()
     
       
    def recoverItemsFromChannels(self):
        self.log('recoverItemsFromChannels')
        ##re-enable library.json items from channels.json
        for type in CHAN_TYPES: 
            if self.monitor.waitForAbort(0.01): break
            items = self.library.getLibraryItems(type)
            if not items: continue
            channels = self.channels.getPredefinedChannelsByType(type)
            if not channels: continue
                
            selects = []
            for idx, item in enumerate(items):
                for channel in channels:
                    if channel.get('name','').lower() == item.get('name','').lower():
                        selects.append(idx)
                        
            self.log('recoverItemsFromChannels, type = %s, selects = %s'%(type,selects))
            if selects: 
                self.library.setEnableStates(type, selects, items)
        PROPERTIES.setPropertyBool('pendingChange',True)
        self.log('recoverItemsFromChannels, finished')
        return True
        
       
    def buildImports(self, items):
        self.log('buildImports')
        self.channels.setImports(items)
        return self.saveChannels()


    def buildPredefinedChannels(self, libraryItems):
        # convert enabled library.json into channels.json items
        # types = list(filter(lambda k:k != LANGUAGE(30033), CHAN_TYPES)) #ignore Imports, use buildImports
    
        def findChannel():
            for idx, eitem in enumerate(echannels):
                if (citem['id'] == eitem['id']) or (citem['type'].lower() == eitem['type'].lower() and citem['name'].lower() == eitem['name'].lower()):
                    return idx, eitem
            return None, {}
                
        def buildAvailableRange():
            # create number array for given type, excluding existing channel numbers.
            start = ((CHANNEL_LIMIT+1)*(CHAN_TYPES.index(type)+1))
            stop  = (start + CHANNEL_LIMIT)
            self.log('buildAvailableRange, type = %s, range = %s-%s, enumbers = %s'%(type,start,stop,enumbers))
            # return list(set(range(start,stop)).difference(set(blist))) #set bug with even array in bytes? 
            return [num for num in range(start,stop) if num not in enumbers]
                
        for type, items in libraryItems.items():
            self.log('buildPredefinedChannels, type = %s'%(type))
            echannels = list(filter(lambda k:k['type'] == type, self.channels.getPredefinedChannels()))    # existing channels, avoid duplicates, aid in removal.
            enumbers  = [echannel.get('number') for echannel in echannels if echannel.get('number',0) > 0] # existing channel numbers
            numbers   = iter(buildAvailableRange()) #list of available channel numbers 
            leftovers = echannels.copy()
            
            for item in items:
                citem = self.channels.getCitem()
                citem.update({'name'   :getChannelSuffix(item['name'], type),
                              'path'   :item['path'],
                              'type'   :item['type'],
                              'logo'   :item['logo'],#todo channels.json no dynamic logo meta, only manager assigned logos.
                              'group'  :[type]})
                citem['group']   = list(set(citem['group']))
                citem['radio']   = (item['type'] == LANGUAGE(30097) or 'musicdb://' in item['path'])
                citem['catchup'] = ('vod' if not citem['radio'] else '')
                
                match, eitem = findChannel()
                if match is not None: #update new citems with existing values.
                    if eitem in leftovers: leftovers.remove(eitem)
                    for key in ['rules','number','favorite','page']: 
                        citem[key] = eitem[key]
                else: citem['number'] = next(numbers,0)
                citem['id'] = getChannelID(citem['name'],citem['path'],citem['number'])
                self.channels.add(citem)

            for eitem in leftovers:
                self.removeChannel(eitem) #remove channels unselected
        self.log('buildPredefinedChannels, finished building')
        return self.saveChannels()
        
        
    def autoPagination(self, id, path, limits={}):
        cacheName = '%s.autoPagination.%s.%s'%(ADDON_ID,id,path)
        if not limits:
            msg = 'get'
            try:    limits = self.channels.getPage(id)
            except: limits = ''
            limits = (limits or self.cache.get(cacheName, json_data=True) or {"end": 0, "start": 0, "total": 0})
        else:
            msg = 'set'
            if self.channels.setPage(id, limits): self.saveChannels()
            self.cache.set(cacheName, limits, expiration=datetime.timedelta(days=SETTINGS.getSettingInt('Max_Days')), json_data=True)
        self.log("%s autoPagination, id = %s, path = %s, limits = %s"%(msg,id,path,limits))
        return limits
            
            
    @staticmethod
    def syncCustom(): #todo sync user created smartplaylists/nodes for multi-room.
        for type in ['library','playlists']:
            for media in ['video','music','mixed']:
                path  = 'special://userdata/%s/%s/'%(type,media)
                files = FileAccess.listdir(path)[1]
                for file in files:
                    orgpath  = os.path.join(path,file)
                    copypath = os.path.join(PLS_LOC,type,media,file)
                    self.log('copyNodes, orgpath = %s, copypath = %s'%(orgpath,copypath))
                    yield FileAccess.copy(orgpath, copypath)


class XMLTV:
    def __init__(self, writer=None):
        log('XMLTV: __init__')
        if writer:
            self.writer = writer
        else:
            self.writer = Writer()
            
        self.vault      = self.writer.vault
        self.dialog     = self.writer.dialog
        self.filelock   = self.writer.GlobalFileLock
        
        if not self.vault.xmltvList:
            self.vault.xmltvList = self.load()
            
            
    def clear(self):
        log('XMLTV: clear')
        self.vault.xmltvList = {}
        return self.deposit()
        

    def reload(self):
        log('XMLTV: reload')
        self.vault.xmltvList = self.load()
        return self.deposit()
        
        
    def deposit(self):
        log('XMLTV: deposit')
        self.vault.set_xmltvList(self.vault.xmltvList)
        return True
        
    
    def withdraw(self):
        log('XMLTV: withdraw')
        return self.vault.get_xmltvList()
     

    def load(self):
        log('XMLTV: load')
        return {'data'       : self.loadData(),
                'channels'   : self.sortChannels(self.cleanSelf(self.loadChannels(),'id')),
                'programmes' : self.sortProgrammes(self.cleanProgrammes(self.cleanSelf(self.loadProgrammes(),'channel')))}
        
        
    def loadData(self):
        log('XMLTV: loadData')
        try: 
            with fileLocker(self.filelock):
                return (xmltv.read_data(FileAccess.open(getUserFilePath(XMLTVFLE), 'r')) or self.resetData())
        except Exception as e: 
            log('XMLTV: loadData, failed! %s'%(e))
            return self.resetData()


    def loadChannels(self, file=getUserFilePath(XMLTVFLE)):
        log('XMLTV: loadChannels, file = %s'%file)
        try:
            with fileLocker(self.filelock):
                return self.sortChannels(xmltv.read_channels(FileAccess.open(file, 'r')) or [])
        except Exception as e:
            if 'no element found: line 1, column 0' in str(e): return [] #new file error
            log('XMLTV: loadChannels, failed! %s'%(e))
            return []
        
        
    def loadProgrammes(self, file=getUserFilePath(XMLTVFLE)):
        log('XMLTV: loadProgrammes, file = %s'%file)
        try: 
            with fileLocker(self.filelock):
                return self.sortProgrammes(xmltv.read_programmes(FileAccess.open(file, 'r')) or [])
        except Exception as e: 
            if 'no element found: line 1, column 0' in str(e): return [] #new file error
            log('XMLTV: loadProgrammes, failed! %s'%(e))
            return []


    def save(self, reset=True):
        log('XMLTV: save')
        if reset: 
            data = self.resetData()
        else:     
            data = self.vault.xmltvList['data']
            
        with fileLocker(self.filelock):
            writer = xmltv.Writer(encoding=DEFAULT_ENCODING, 
                                  date                = data['date'],
                                  source_info_url     = data['source-info-url'], 
                                  source_info_name    = data['source-info-name'],
                                  generator_info_url  = data['generator-info-url'], 
                                  generator_info_name = data['generator-info-name'])
                   
            channels = self.sortChannels(self.vault.xmltvList['channels'])
            for channel in channels: writer.addChannel(channel)

            programmes = self.sortProgrammes(self.vault.xmltvList['programmes'])
            for program in programmes: writer.addProgramme(program)
            
            filePath = getUserFilePath(XMLTVFLE)
            log('XMLTV: save, saving to %s'%(filePath))
            writer.write(FileAccess.open(filePath, "w"), pretty_print=True)
            self.buildGenres()
        return self.reload()
        

    def delete(self):
        log('XMLTV: delete')
        if FileAccess.delete(getUserFilePath(XMLTVFLE)): #xmltv.xml
            FileAccess.delete(getUserFilePath(GENREFLE)) #genre.xml
            return self.dialog.notificationDialog(LANGUAGE(30016)%('XMLTV'))
        return False


    @staticmethod
    def cleanSelf(items, key='id', slug='@%s'%(slugify(ADDON_NAME))): # remove imports (Non PseudoTV Live), key = {'id':channels,'channel':programmes}
        log('XMLTV: cleanSelf, key = %s'%(key))
        if not slug: return items
        return list(filter(lambda item:item.get(key,'').endswith(slug), items))
        
        
    @staticmethod
    def cleanProgrammes(programmes): # remove expired content
        try:
            now = (datetime.datetime.fromtimestamp(float(getLocalTime()))) - datetime.timedelta(hours=3) #allow some old programmes to avoid empty cells.
            tmpProgrammes = [program for program in programmes if strpTime(program['stop'].rstrip(),DTFORMAT)  > now]
        except Exception as e: 
            log("cleanProgrammes, Failed! " + str(e), xbmc.LOGERROR)
            tmpProgrammes = programmes
        log('XMLTV: cleanProgrammes, before = %s, after = %s'%(len(programmes),len(tmpProgrammes)))
        return tmpProgrammes


    @staticmethod
    def sortChannels(channels):
        try: channels.sort(key=lambda x:x.get('display-name'))
        except: pass
        log('XMLTV: sortChannels, channels = %s'%(len(channels)))
        return channels


    @staticmethod
    def sortProgrammes(programmes):
        programmes.sort(key=lambda x:x['start'])
        programmes.sort(key=lambda x:x['channel'])
        log('XMLTV: sortProgrammes, programmes = %s'%(len(programmes)))
        return programmes


    def importXMLTV(self, file, slug=None):
        log('XMLTV: importXMLTV, file = %s'%file)
        try:
            if file.startswith('http'):
                url  = file
                file = os.path.join(TEMP_LOC,'%s.xml'%(slugify(url)))
                saveURL(url,file)
            self.vault.xmltvList['channels'].extend(self.sortChannels(self.cleanSelf(self.loadChannels(file),'id',slug)))#todo collision logic?
            self.vault.xmltvList['programmes'].extend(self.sortProgrammes(self.cleanSelf(self.loadProgrammes(file),'channel',slug)))
        except Exception as e: self.log("XMLTV: importXMLTV, failed! " + str(e), xbmc.LOGERROR)
        return True


    def buildGenres(self):
        log('XMLTV: buildGenres') #todo user color selector.
        with fileLocker(self.filelock):
            dom = parse(FileAccess.open(GENREFLE_DEFAULT, "r"))
        
        epggenres = {}
        lines = dom.getElementsByTagName('genre')
        for line in lines: 
            items = line.childNodes[0].data.split('/')
            for item in items:
                epggenres[item.strip()] = line.attributes['genreId'].value
            
        proggenres = []
        for program in self.vault.xmltvList['programmes']:
            group = []
            for genre in program.get('category',[]):
                group.append(genre[0])
            proggenres.append(group)
            
        for genres in proggenres:
            for genre in genres:
                if epggenres.get(genre,''):#{'Drama': '0x81'}
                    epggenres[('/').join(genres)] = epggenres.get(genre,'0x00')
                    break
                    
        doc  = Document()
        root = doc.createElement('genres')
        doc.appendChild(root)
        name = doc.createElement('name')
        name.appendChild(doc.createTextNode('%s Genres using Hexadecimal for genreId'%(ADDON_NAME)))
        root.appendChild(name)
        [root.appendChild(line) for line in lines] #append org. genre.xml list
        
        for key in epggenres:
            gen = doc.createElement('genre')
            gen.setAttribute('genreId',epggenres[key])
            gen.appendChild(doc.createTextNode(key))
            root.appendChild(gen)
        
        with fileLocker(self.filelock):
            xmlData = FileAccess.open(getUserFilePath(GENREFLE), "w")
            xmlData.write(doc.toprettyxml(indent='\t'))
            xmlData.close()
        return True


    def getChannels(self):
        log('XMLTV: getChannels')
        return self.vault.xmltvList.get('channels',[])


    def getProgrammes(self):
        log('XMLTV: getProgrammes')
        return self.vault.xmltvList.get('programmes',[])


    def getEndtimes(self): 
        endtime    = {} # get "Endtime" channels last stopDate in programmes
        channels   = self.sortChannels(self.vault.xmltvList['channels'])
        programmes = self.sortProgrammes(self.vault.xmltvList['programmes'])
        for channel in channels:
            try: 
                stopDate = max([strpTime(program['stop'], DTFORMAT).timetuple() for program in programmes if program['channel'] == channel['id']])
                stopTime = time.mktime(stopDate)
                endtime[channel['id']] = stopTime
            except Exception as e: 
                log("XMLTV: getEndtimes, Failed! " + str(e), xbmc.LOGERROR)
                self.removeChannel(channel['id'])
        return endtime
         
         
    def resetData(self):
        log('XMLTV: resetData')
        return {'date'                : datetime.datetime.fromtimestamp(float(time.time())).strftime(DTFORMAT),
                'generator-info-name' : self.cleanString('%s Guidedata'%(ADDON_NAME)),
                'generator-info-url'  : self.cleanString(ADDON_ID),
                'source-info-name'    : self.cleanString(ADDON_NAME),
                'source-info-url'     : self.cleanString(ADDON_ID)}


    def addChannel(self, item, update=False):
        citem    = ({'id'           : item['id'],
                     'display-name' : [(self.cleanString(item['name']), LANG)],
                     'icon'         : [{'src':item['logo']}]})
        log('XMLTV: addChannel, update = %s, citem = %s'%(update,citem))
        idx, channel = self.findChannel(citem, self.vault.xmltvList['channels'])
        if idx is None: self.vault.xmltvList['channels'].append(citem)
        else:
            if update:
                self.vault.xmltvList['channels'][idx].update(citem) # update existing channel meta
            else:
                self.vault.xmltvList['channels'][idx] = citem       # replace existing channel meta
        return True


    def addProgram(self, id, item):
        pitem      = {'channel'     : id,
                      'credits'     : {'writer':[setWriter(self.cleanString(item['writer']),encodeString(dumpJSON(item['fitem'])))]},
                      'category'    : [(self.cleanString(genre.replace('Unknown','Undefined')),LANG) for genre in item['categories']],
                      'title'       : [(self.cleanString(item['title']), LANG)],
                      'desc'        : [(self.cleanString(item['desc']), LANG)],
                      'star-rating' : [{'value': self.cleanStar(item['stars'])}],
                      'stop'        : (datetime.datetime.fromtimestamp(float(item['stop'])).strftime(DTFORMAT)),
                      'start'       : (datetime.datetime.fromtimestamp(float(item['start'])).strftime(DTFORMAT)),
                      'icon'        : [{'src': item['thumb']}],
                      'length'      : {'units': 'seconds', 'length': str(item['length'])}}
                      
        if item.get('sub-title',''):
            pitem['sub-title'] = [(self.cleanString(item['sub-title']), LANG)]

        if item.get('director',''):
            pitem['credits']['director'] = [self.cleanString(item['director'])]

        if item.get('catchup-id',''):
            pitem['catchup-id'] = item['catchup-id']
            
        if item.get('date',''):
            try: pitem['date'] = (strpTime(item['date'], '%Y-%m-%d')).strftime('%Y%m%d')
            except: pass

        if item.get('new',False): 
            pitem['new'] = '' #write blank tag, tag == True
        
        rating = self.cleanMPAA(item.get('rating',''))
        if rating != 'NA' and rating.startswith('TV'): 
            pitem['rating'] = [{'system': 'VCHIP', 'value': rating}]
        elif rating != 'NA' :  
            pitem['rating'] = [{'system': 'MPAA', 'value': rating}]
            
        if item.get('episode-num',''): 
            pitem['episode-num'] = [(item['episode-num'], 'onscreen')]
            
        if item.get('audio',[]):
            pitem['audio'] = {'stereo': item.get('audio',[])[0]}

        if item.get('video',[]):
            pitem['video'] = {'aspect': item.get('video',[])[0]}
        
        if item.get('language',[]):
            pitem['language'] = (item.get('language',[])[0], LANG)
           
        if item.get('subtitle',[]): #needed?
            pitem['subtitles'] = [{'type': 'teletext', 'language': ('%s'%(sub), LANG)} for sub in item.get('subtitle',[])]
            
         ##### TODO #####
           # 'country'     : [('USA', LANG)],#todo
           # 'premiere': (u'Not really. Just testing', u'en'),
            
        log('XMLTV: addProgram = %s'%(pitem))
        self.vault.xmltvList['programmes'].append(pitem)
        return True


        
    def removeChannel(self, id): # remove single channel and all programmes from xmltvList
        channels   = self.vault.xmltvList['channels'].copy()
        programmes = self.vault.xmltvList['programmes'].copy()
        self.vault.xmltvList['channels']   = list(filter(lambda channel:channel.get('id','') != id, channels))
        self.vault.xmltvList['programmes'] = list(filter(lambda program:program.get('channel','') != id, programmes))
        log('XMLTV: removeChannel, removing channel %s; channels: before = %s, after = %s; programmes: before = %s, after = %s'%(id,len(channels),len(self.vault.xmltvList['channels']),len(programmes),len(self.vault.xmltvList['programmes'])))
        return True
        
        
    @staticmethod
    def findChannel(item, channels): #find existing channel id in xmltvList
        for idx, channel in enumerate(channels): 
            if channel['id'] == item['id']: 
                return idx, channel
        return None, {}
        

    @staticmethod
    def cleanStar(str1):
        return '%s/10'%(int(round(float(str1))))


    @staticmethod
    def cleanMPAA(str1):
        #todo regex, detect other region rating formats
        # re.compile(':(.*)', re.IGNORECASE).search(str1.split('Rated ')[1])
        try: return str1.split('Rated ')[1]
        except: return str1


    @staticmethod
    def cleanString(text):
        if text == ',' or not text: text = LANGUAGE(30161) #"Unavailable"
        return text
        
class M3U:
    def __init__(self, writer=None):
        log('M3U: __init__')
        if writer:
            self.writer = writer
        else:
            self.writer = Writer()
            
        self.vault      = self.writer.vault
        self.monitor    = self.writer.monitor
        self.filelock   = self.writer.GlobalFileLock
        
        if not self.vault.m3uList:
            self.vault.m3uList = self.load()
            

    def clear(self):
        log('M3U: clear')
        self.vault.m3uList  = {}
        return self.deposit()
        
        
    def reload(self):
        log('M3U: reload')
        self.vault.m3uList = self.load()
        return self.deposit()
        
     
    def deposit(self):
        log('M3U: deposit')
        self.vault.set_m3uList(self.vault.m3uList)
        return True
        
    
    def withdraw(self):
        log('M3U: withdraw')
        return self.vault.get_m3uList()
     

    def load(self):
        log('M3U: load')
        return {'data':'#EXTM3U tvg-shift="%s" x-tvg-url="" x-tvg-id=""'%(self.getShift()),
                'channels':self.cleanSelf(self.loadM3U())}
        

    def loadM3U(self, file=getUserFilePath(M3UFLE)):
        log('M3U: loadM3U, file = %s'%file)
        if file.startswith('http'):
            url  = file
            file = os.path.join(TEMP_LOC,slugify(url),'.m3u')
            saveURL(url,file)
            
        with fileLocker(self.filelock):
            fle   = FileAccess.open(file, 'r')
            lines = (fle.readlines())
            data  = lines.pop(0)
            fle.close()
            
        chCount = 0
        for idx, line in enumerate(lines):
            line = line.rstrip()
            if line.startswith('#EXTINF:'):
                chCount += 1
                match = {'number' :re.compile('tvg-chno=\"(.*?)\"'   , re.IGNORECASE).search(line),
                         'id'     :re.compile('tvg-id=\"(.*?)\"'     , re.IGNORECASE).search(line),
                         'name'   :re.compile('tvg-name=\"(.*?)\"'   , re.IGNORECASE).search(line),
                         'logo'   :re.compile('tvg-logo=\"(.*?)\"'   , re.IGNORECASE).search(line),
                         'group'  :re.compile('group-title=\"(.*?)\"', re.IGNORECASE).search(line),
                         'radio'  :re.compile('radio=\"(.*?)\"'      , re.IGNORECASE).search(line),
                         'catchup':re.compile('catchup=\"(.*?)\"'    , re.IGNORECASE).search(line),
                         'label'  :re.compile(',(.*)'                , re.IGNORECASE).search(line),
                         'shift'  :re.compile('tvg-shift=\"(.*?)\"'  , re.IGNORECASE).search(line)}#todo shift timestamp delta to localtime
                
                item  = {'number'    :chCount,
                         'logo'      :LOGO,
                         'radio'     :'false',
                         'catchup'   :'',
                         'group'     :[],
                         'kodiprops' :[]}
                         
                for key in match.keys():
                    if not match[key]: continue
                    item[key] = match[key].group(1)
                    if key == 'number':
                        try:    item[key] = int(item[key])
                        except: item[key] = float(item[key])
                    elif key == 'group':
                        item[key] = item[key].split(';')
                        try: item[key].remove(ADDON_NAME)
                        except: pass
                        finally: 
                            item[key] = list(filter(None,list(set(item[key]))))
                    elif key == 'radio':
                        item[key] = item[key].lower() == 'true'

                for nidx in range(idx+1,len(lines)):
                    nline = lines[nidx].rstrip()
                    if   nline.startswith('#EXTINF:'): break
                    elif nline.startswith('#KODIPROP:'):
                        prop = re.compile('^#KODIPROP:(.*)$', re.IGNORECASE).search(nline)
                        if prop: item['kodiprops'].append(prop.group(1))
                    elif nline.startswith('##'): continue
                    elif not nline: continue
                    else: item['url'] = nline
                        
                item['name']  = (item.get('name','')  or item.get('label',''))
                item['label'] = (item.get('label','') or item.get('name',''))
                if not item.get('id','') or not item.get('name','') or not item.get('number',''): 
                    log('M3U: load, SKIPPED MISSING META item = %s'%item)
                    continue
                log('M3U: load, item = %s'%item)
                yield item
                    

    def save(self):
        log('M3U: save')
        with fileLocker(self.filelock):
            filePath = getUserFilePath(M3UFLE)
            fle = FileAccess.open(filePath, 'w')
            log('M3U: save, saving to %s'%(filePath))
            fle.write('%s\n'%(self.vault.m3uList['data']))
            citem = '#EXTINF:-1 tvg-chno="%s" tvg-id="%s" tvg-name="%s" tvg-shift="%s" tvg-logo="%s" group-title="%s" radio="%s" catchup="%s",%s\n'
            channels = self.sortChannels(self.vault.m3uList['channels'])
            for channel in channels:
                if not channel: continue
                fle.write(citem%(channel['number'],
                                 channel['id'],
                                 channel['name'],
                                 channel.get('shift',0),#opt from user imports, not used internally. #todo shift timestamp
                                 channel['logo'],
                                 ';'.join(channel['group']),
                                 channel['radio'],
                                 channel['catchup'],
                                 channel['label']))
                if channel.get('kodiprops',[]):
                    fle.write('%s\n'%('\n'.join(['#KODIPROP:%s'%(prop) for prop in channel['kodiprops']])))
                fle.write('%s\n'%(channel['url']))
            fle.close()
        return self.reload()
        
        
    def delete(self):
        log('M3U: delete')
        if FileAccess.delete(getUserFilePath(M3UFLE)): return self.dialog.notificationDialog(LANGUAGE(30016)%('M3U'))
        return False
        
        
    @staticmethod
    def cleanSelf(channels, slug='@%s'%(slugify(ADDON_NAME))):
        log('M3U: cleanSelf, slug = %s'%(slug)) # remove imports (Non PseudoTV Live)
        if not slug: return channels
        return list(filter(lambda line:line.get('id','').endswith(slug), channels))
        
        
    @staticmethod
    def sortChannels(channels):
        return sorted(channels, key=lambda k: k['number'])
        
        
    def importM3U(self, file, slug=None, multiplier=1):
        log('M3U: importM3U, file = %s'%file)
        try:
            if file.startswith('http'):
                url  = file
                file = os.path.join(TEMP_LOC,'%s.m3u'%(slugify(url)))
                saveURL(url,file)
            self.vault.m3uList.get('channels',[]).extend(self.sortChannels(self.cleanSelf(self.chkImport(self.loadM3U(file),multiplier),slug)))
        except Exception as e: log("M3U: importM3U, failed! " + str(e), xbmc.LOGERROR)
        return True
        
        
    def chkImport(self, channels, multiplier=1):
        def roundup(x):
            return x if x % 1000 == 0 else x + 1000 - x % 1000
            
        def frange(start, stop, step):
          while not self.monitor.abortRequested() and start < stop:
            yield float(start)
            start += decimal.Decimal(step)

        channels  = self.sortChannels(channels)
        chstart   = roundup((CHANNEL_LIMIT * len(CHAN_TYPES)+1))
        chmin     = int(chstart + (multiplier*1000))
        chmax     = int(chmin + (CHANNEL_LIMIT))
        chrange   = list(frange(chmin,chmax,0.1))
        leftovers = []
        log('M3U: chkImport, channels = %s, multiplier = %s, chstart = %s, chmin = %s, chmax = %s'%(len(channels),multiplier,chstart,chmin,chmax))
        ## check tvg-chno for conflict, use multiplier to modify org chnum.
        for citem in channels:
            if len(chrange) == 0:
                log('M3U: chkImport, reached max import')
                break
            elif citem['number'] < CHANNEL_LIMIT: 
                newnumber = (chmin+citem['number'])
                if newnumber in chrange:
                    chrange.remove(newnumber)
                    citem['number'] = newnumber
                    yield citem
                else: leftovers.append(citem)
            else: leftovers.append(citem)
        
        for citem in leftovers:
            if len(chrange) == 0:
                log('M3U: chkImport, reached max import')
                break
            else:
                citem['number'] = chrange.pop(0)
                yield citem
            
            
    def getShift(self):
        log('M3U: getShift')
        return '' # '-%s'%((round(datetime.datetime.now().minute) / 60)[:3])

    
    def getChannels(self):
        log('M3U: getChannels')
        return self.sortChannels(self.vault.m3uList.get('channels',[]))
        
        
    def addChannel(self, item, update=False):
        log('M3U: addChannel, update = %s, item = %s'%(update,item))
        idx, line = self.findChannel(item['id'])
        if idx is None: self.vault.m3uList['channels'].append(item)
        else:
            if update: 
                self.vault.m3uList['channels'][idx].update(item) # update existing channel
            else: 
                self.vault.m3uList['channels'][idx] = item       # replace existing channel
        return True


    def findChannel(self, id):
        channels = self.vault.m3uList['channels']
        for idx, line in enumerate(channels):
            if line.get('id','') == id:
                log('M3U: findChannel, idx = %s, line = %s'%(idx, line))
                return idx, line
        return None, {}
        
        
    def removeChannel(self, id=''):
        idx, line = self.findChannel(id)
        if idx is not None: 
            log('M3U: removeChannel, removing %s'%(line))
            self.vault.m3uList['channels'].remove(line)
            return True
        return False
        
        