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

from resources.lib.globals  import *
from resources.lib.rules    import RulesList

class Plugin:
    currentChannel  = ''
    channelItem     = {}
    channelPlaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    
    def __init__(self, sysARG=sys.argv, service=None):
        self.log('__init__, sysARG = ' + str(sysARG))
        self.sysARG         = sysARG
        self.CONTENT_TYPE   = 'episodes'
        self.CACHE_ENABLED  = True
        self.setOffset      = False #todo adv. channel rule to disable seek 
        
        if service is None:
            from resources.lib.jsonrpc import JSONRPC
            self.dialog     = Dialog()
            self.jsonRPC    = JSONRPC()
            self.rules      = RulesList()
            self.player     = xbmc.Player()
            self.monitor    = xbmc.Monitor()
        else:
            self.dialog     = service.dialog
            self.jsonRPC    = service.jsonRPC
            self.rules      = service.rules
            self.player     = service.myPlayer
            self.monitor    = service.myMonitor
        
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        return log('%s: %s'%(self.__class__.__name__,msg),level)


    def runActions(self, action, citem, parameter=None):
        self.log("runActions action = %s, channel = %s"%(action,citem))
        if not citem.get('id',''): return parameter
        ruleList = self.rules.loadRules([citem]).get(citem['id'],[])
        for rule in ruleList:
            if action in rule.actions:
                self.log("runActions performing channel rule: %s"%(rule.name))
                return rule.runAction(action, self, parameter)
        return parameter


    def buildMenu(self, name=None):
        self.log('buildMenu, name = %s'%name)
        MAIN_MENU = [(LANGUAGE(30008), '', '')]#"Channels"

        UTIL_MENU = [#(LANGUAGE(30010), '', '', LANGUAGE(30008)),#"Rebuild M3U/XMLTV"
                     (LANGUAGE(30011), '', '', LANGUAGE(30008)),#"Delete [M3U/XMLTV/Genre]"
                     (LANGUAGE(30096), '', '', LANGUAGE(30008)),#"Clean Start, Delete [Channels/Settings/M3U/XMLTV/Genre]"
                     (LANGUAGE(30012)%(self.jsonRPC.getPluginMeta(PVR_CLIENT).get('name',''),ADDON_NAME,), '', '', LANGUAGE(30008)), #"Reconfigure PVR for use with PTVL"
                     (LANGUAGE(30065)%(self.jsonRPC.getPluginMeta(PVR_CLIENT).get('name','')), '', '', LANGUAGE(30008)),#"Force PVR reload"
                     (LANGUAGE(30013), '', '', LANGUAGE(30008))]#"Open Settings"

        if   name is None:            items = MAIN_MENU
        elif name == LANGUAGE(30008): items = UTIL_MENU
        else: return
        [self.addDir(*item) for item in items]
        
        
    def deleteFiles(self, msg, full=False):
        self.log('deleteFiles, full = %s'%(full))
        setBusy(True)
        files = {LANGUAGE(30172):getUserFilePath(M3UFLE),LANGUAGE(30173):getUserFilePath(XMLTVFLE),LANGUAGE(30009):getUserFilePath(CHANNELFLE),LANGUAGE(30130):SETTINGS_FLE,LANGUAGE(30179):getUserFilePath(LIBRARYFLE)}
        keys  = [LANGUAGE(30172),LANGUAGE(30173),LANGUAGE(30009),LANGUAGE(30130),LANGUAGE(30179)]
        if not full: keys = keys[:3]
        if self.dialog.yesnoDialog('%s ?'%(msg)): [self.dialog.notificationDialog(LANGUAGE(30016)%(key)) for key in keys if FileAccess.delete(files[key])]
        PROPERTIES.setPropertyBool('autotuned',False)
        if full: return self.dialog.okDialog(LANGUAGE(30183))
        setBusy(False)
        return True

            
    def utilities(self, name):
        self.log('utilities, name = %s'%name)
        with busy():
            if   name == LANGUAGE(30011): self.deleteFiles(name)
            elif name == LANGUAGE(30096): self.deleteFiles(name, full=True)
            elif name == LANGUAGE(30012)%(self.jsonRPC.getPluginMeta(PVR_CLIENT).get('name',''),ADDON_NAME,): configurePVR()
            elif name == LANGUAGE(30065)%(self.jsonRPC.getPluginMeta(PVR_CLIENT).get('name','')): brutePVR()
            elif name == LANGUAGE(30013): REAL_SETTINGS.openSettings()
            else: return
        xbmc.executebuiltin('Action(Back,10025)')
            

    def addLink(self, name, channel, path, mode='',icon=ICON, liz=None, total=0):
        if liz is None:
            liz=xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
            liz.setArt({'thumb':icon,'logo':icon,'icon':icon})
        self.log('addLink, name = %s'%(name))
        u=self.sysARG[0]+"?url="+urllib.parse.quote(path)+"&channel="+str(channel)+"&name="+urllib.parse.quote(name)+"&mode="+str(mode)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, channel, path, mode='',icon=ICON, liz=None):
        self.log('addDir, name = %s'%(name))
        if liz is None:
            liz=xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
            liz.setArt({'thumb':icon,'logo':icon,'icon':icon})
        liz.setProperty('IsPlayable', 'false')
        u=self.sysARG[0]+"?url="+urllib.parse.quote(path)+"&channel="+str(channel)+"&name="+urllib.parse.quote(name)+"&mode="+str(mode)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
     

    def contextPlay(self, writer, isPlaylist=False):
        channelData = writer.get('citem',{})
        if channelData: 
            stpos   = 0
            pvritem = self.jsonRPC.getPVRposition(channelData.get('name',''), channelData.get('id',''), isPlaylist=isPlaylist)
            self.log('contextPlay, writer = %s, pvritem = %s, isPlaylist = %s'%(writer,pvritem,isPlaylist))
            self.channelPlaylist.clear()
            xbmc.sleep(100)
            
            if isPlaylist:
                nowitem = pvritem.get('broadcastnow',{})
                liz = buildItemListItem(getWriter(nowitem.get('writer','')))
                liz.setProperty('pvritem', dumpJSON(pvritem))
                setCurrentChannelItem(pvritem)
                
                listitems = [liz]
                nextitems = pvritem.get('broadcastnext',[])
                del nextitems[PAGE_LIMIT:]# list of upcoming items, truncate for speed.
                
                listitems.extend([buildItemListItem(getWriter(nextitem.get('writer',''))) for nextitem in nextitems])
                nextitems.insert(0,nowitem)
                
                for pos, nextitem in enumerate(nextitems):
                    if getWriter(nextitem.get('writer',{})).get('file','') == writer.get('file',''):
                        stpos = pos
                        break
            else:
                liz = buildItemListItem(writer)
                liz.setProperty('pvritem', dumpJSON(pvritem))
                setCurrentChannelItem(pvritem)
                listitems = [liz]
                stpos = 0
                
            self.log('contextPlay, writer stpos = %s, playlist = %s'%(stpos,len(listitems)))
            [self.channelPlaylist.add(lz.getPath(),lz,idx) for idx,lz in enumerate(listitems)]
            if isPlaylistRandom(): self.channelPlaylist.unshuffle()
            return self.player.play(self.channelPlaylist, startpos=stpos)

        self.dialog.notificationDialog(LANGUAGE(30001))
        return xbmcplugin.setResolvedUrl(int(self.sysARG[1]), False, xbmcgui.ListItem())
        
        
    def playRadio(self, name, id):
        self.log('playRadio, id = %s'%(id))
        pvritem = self.jsonRPC.getPVRposition(name, id, radio=True)
        nowitem = pvritem.get('broadcastnow',{}) # current item
        
        if nowitem:
            writer   = getWriter(nowitem.get('writer',{}))
            response = self.jsonRPC.requestList(id, writer.get('citem',{}).get('path',''), 'music', page=RADIO_ITEM_LIMIT)
            if response:
                self.channelPlaylist.clear()
                xbmc.sleep(100)
                
                nextitems = response
                random.shuffle(nextitems)
                nowitem   = nextitems.pop(0)
                
                liz = buildItemListItem(nowitem, mType='music')
                liz.setProperty('pvritem', dumpJSON(pvritem))
                setCurrentChannelItem(pvritem)
                
                listitems = [liz]
                listitems.extend([buildItemListItem(nextitem, mType='music') for nextitem in nextitems])
                [self.channelPlaylist.add(lz.getPath(),lz,idx) for idx,lz in enumerate(listitems)]
                if not isPlaylistRandom(): self.channelPlaylist.shuffle()
                self.log('playRadio, Playlist size = %s'%(self.channelPlaylist.size()))
                return self.player.play(self.channelPlaylist)

        self.dialog.notificationDialog(LANGUAGE(30001))
        return xbmcplugin.setResolvedUrl(int(self.sysARG[1]), False, xbmcgui.ListItem())

        
    def playChannel(self, name, id, isPlaylist=False, failed=False):
        self.log('playChannel, id = %s, isPlaylist = %s'%(id,isPlaylist))
        found     = False
        listitems = [xbmcgui.ListItem()] #empty listitem required to pass failed playback.
        
        if self.currentChannel != id: self.currentChannel = id
        pvritem   = self.jsonRPC.getPVRposition(name, id, isPlaylist=isPlaylist)
        nowitem   = pvritem.get('broadcastnow',{})  # current item
        nextitems = pvritem.get('broadcastnext',[]) # upcoming items
        citem     = getWriter(nowitem.get('writer',{})).get('citem',{})
        pvritem['citem'].update(citem) #update citem with comprehensive meta
        del nextitems[PAGE_LIMIT:]# list of upcoming items, truncate for speed.
         
        if nowitem:
            found    = True
            lastitem = PROPERTIES.getPropertyDict('Last_Item')
            if nowitem != lastitem: #detect loopback
                nowitem   = self.runActions(RULES_ACTION_PLAYBACK, citem, nowitem)
                percent   = round(nowitem['progresspercentage'])
                progress  = nowitem['progress']
                runtime   = nowitem['runtime']
                seekTHLD  = SETTINGS.getSettingInt('Seek_Threshold%')
                seekTLRNC = SETTINGS.getSettingInt('Seek_Tolerance')
            
                if progress > seekTLRNC:
                    self.log('playChannel, progresspercentage = %s, seekThreshold = %s'%(percent,seekTHLD))
                    if percent >= seekTHLD:  # near end, avoid callback; override nowitem and queue next show.
                        self.log('playChannel, progress near the end, queue nextitem')
                        nowitem = nextitems.pop(0) #remove first element in nextitems keep playlist order.
                    else: 
                        self.setOffset = True #channel requires offset for "PseudoTV" effect.
                        
            else: 
                nowitem = nextitems.pop(0)
                self.log('playChannel, loopback detected advancing queue to nextitem')
            PROPERTIES.setPropertyDict('Last_Item',nowitem)
          
            self.log('playChannel, nowitem = %s\ncitem = %s'%(nowitem,citem))
                
            writer = getWriter(nowitem.get('writer',{}))
            liz = buildItemListItem(writer)
            
            if self.setOffset:
                self.log('playChannel, within seek tolerance setting seek totaltime = %s, resumetime = %s'%((runtime * 60),progress))
                pvritem['progress'] = progress
                pvritem['runtime']  = runtime
                liz.setProperty('totaltime'  , str((runtime * 60))) #sec
                liz.setProperty('resumetime' , str(progress))       #sec
                liz.setProperty('startoffset', str(progress))       #sec
                
                url  = liz.getPath()
                file = writer.get('originalfile','')
                if isStack(url) and not hasStack(url,file):
                    self.log('playChannel, playing stack with url = %s'%(url))
                    liz.setPath('stack://%s'%(' , '.join(stripStack(url, file))))#remove pre-roll stack from seek offset video.

            liz.setProperty('pvritem',dumpJSON(pvritem))
            listitems = [liz]
            
            ## #todo drop setCurrentChannelItem for class var.
            setCurrentChannelItem(pvritem)
            self.channelItem = pvritem
            ##
            
            if isPlaylist:
                self.channelPlaylist.clear()
                lastitem  = nextitems.pop(-1)
                lastwrite = getWriter(lastitem.get('writer',''))
                lastwrite['file'] = 'plugin://%s/?mode=play&name=%s&id=%s&radio=False'%(ADDON_ID,name,id) #pvritem.get('callback')
                lastitem['writer'] = setWriter('Unavailable',encodeString(dumpJSON(lastwrite)))
                nextitems.append(lastitem) #insert pvr callback
                listitems.extend([buildItemListItem(getWriter(nextitem.get('writer',''))) for nextitem in nextitems])
                for idx,lz in enumerate(listitems): self.channelPlaylist.add(lz.getPath(),lz,idx)
                if isPlaylistRandom(): self.channelPlaylist.unshuffle()
                self.log('playChannel, Playlist size = %s'%(self.channelPlaylist.size()))
                return self.player.play(self.channelPlaylist)  
                
            # if isStack(listitems[0].getPath()):
                # url = 'plugin://%s/?mode=vod&name=%s&id=%s&channel=%s&radio=%s'%(ADDON_ID,quote(listitems[0].getLabel()),quote(encodeString(listitems[0].getPath())),quote(citem['id']),'False')
                # self.log('playChannel, isStack calling playVOD url = %s'%(url))
                # listitems[0].setPath(url) #test to see if stacks play better as playmedia.
                # return self.player.play(listitems[0].getPath(),listitems[0])
                
            # listitems = []
            # paths = splitStacks(liz.getPath())
            # paths.append(pvritem['callback'])
            # listitems[0].setPath('stack://%s'%(' , '.join(url)))
            
            # for idx,path in enumerate(paths):
                # print(idx,path)
                # lz = liz
                # lz.setPath(path)
                # listitems.append(lz)
                # print(listitems)
                # self.channelPlaylist.add(path,lz,idx)
            # self.log('playChannel, set callback stack with paths = %s'%(paths))
            
        else: self.dialog.notificationDialog(LANGUAGE(30001))
        return xbmcplugin.setResolvedUrl(int(self.sysARG[1]), found, listitems[0])
        

    def playVOD(self, name, id):
        path = decodeString(id)
        self.log('playVOD, path = %s'%(path))
        # if isStack(path):
            # xbmc.executebuiltin('PlayMedia(%s,resume)'%path)
        # else:
        liz = xbmcgui.ListItem(name,path=path)
        liz.setProperty("IsPlayable","true")
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)


    def getParams(self):
        return dict(urllib.parse.parse_qsl(self.sysARG[2][1:]))


    def run(self):  
        params  = self.getParams()
        name    = (unquote(params.get("name",'')) or None)
        channel = (params.get("channel",'')       or None)
        url     = (params.get("url",'')           or None)
        id      = (params.get("id",'')            or None)
        radio   = (params.get("radio",'')         or 'False') == "True"
        mode    = (params.get("mode",'')          or None)
        self.log("Name = %s, Channel = %s, URL = %s, ID = %s, Radio = %s, Mode = %s"%(name,channel,url,id,radio,mode))

        if   mode is None:  self.buildMenu(name)
        elif mode == 'vod': self.playVOD(name, id)
        elif mode == 'play':
            if radio:
                return self.playRadio(name, id)
            else:
                return self.playChannel(name, id, isPlaylist=bool(SETTINGS.getSettingInt('Playback_Method')))
        elif mode == 'Utilities': self.utilities(name)

        xbmcplugin.setContent(int(self.sysARG[1])    , self.CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=self.CACHE_ENABLED)
       
if __name__ == '__main__': Plugin(sys.argv).run()