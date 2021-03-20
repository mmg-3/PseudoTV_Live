![](https://raw.githubusercontent.com/PseudoTV/PseudoTV_Artwork/master/PseudoTV%20Live/Flat/PTVL%20-%20Metro%20-%20Fanart%20(1).png)

## PseudoTV Live:

PseudoTV Live acts similar to normal broadcast or cable TV, complete with multiple preset, user-defined channels and advanced channel management.

PseudoTV Live can integrate with all Kodi sources including various Kodi plugins ie. Plex, Netflix, etc.
Create rich, in-depth channels with the added feature to import existing M3U/XMLTV pairs.

[Forum](https://forum.kodi.tv/showthread.php?tid=355549)
[Discussion](https://forum.kodi.tv/showthread.php?tid=346803)
[Channel Configuration Example](https://rawhttps://github.com/PseudoTV/PseudoTV_Live/raw/master/plugin.video.pseudotv.live/channels.json.githubusercontent.com/PseudoTV/PseudoTV_Live/master/channels.json)

[![Codacy Badge](https://img.shields.io/codacy/grade/efcc007bd689449f8cf89569ac6a311b.svg?style=flat-square)](https://www.codacy.com/app/PseudoTV/PseudoTV_Live/dashboard)
[![GitHub last commit](https://img.shields.io/github/last-commit/PseudoTV/PseudoTV_Live.svg?style=flat-square)](https://github.com/PseudoTV/PseudoTV_Live/commits/master)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/PseudoTV/PseudoTV_Live.svg?color=red&style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/PseudoTV/PseudoTV_Live.svg?style=flat-square)](https://github.com/PseudoTV/PseudoTV_Live/issues)  
[![Kodi URL](https://img.shields.io/badge/Supports-Kodi%2019-blue.svg?style=flat-square)](https://kodi.tv/download)
[![Kodi Donate](https://img.shields.io/badge/Donate-Kodi-blue.svg?style=flat-square)](https://kodi.tv/contribute/donate)
[![Lunatixz Donate](https://img.shields.io/badge/Coffee-Lunatixz-blue.svg?style=flat-square)](https://www.buymeacoffee.com/Lunatixz)
[![Twitter URL](https://img.shields.io/twitter/follow/PseudoTV_Live.svg?color=blue&label=%40PseudoTV_Live&style=flat-square)](https://twitter.com/PseudoTV_Live) 

------------

#Settings:

##Playback Method: 

1) PVR Callback - This method keeps Kodi believing you're using a Live feed from the PVR backend. Pros| Kodi PVR UI and Widget updates. Near infinite channel playback. Cons| Slower channel content changes. (1-60secs. depending on your system). If "Overlay" is enabled in settings; and active during content change you'll be met with a custom background. (Currently static).

2) Playlist - Standard Kodi playlist queue (not to be confused with a smart playlist). Pros| Channel content changes quickly. Cons| Kodi does not treat playback as PVR channel, Playlist queues are finite.

##- Seek tolerance (Smart Seeking):

Adjusting seek tolerance (in seconds) adds a buffer at the beginning of media that is currently selected to play and which includes an offset for a "Pseudo" Live effect. The greater the number the more it ignores the time differential between "live" and "load" times.
ex. If after a show ends your next show which should start at the beginning starting a few seconds into the future; due to a lag in loading time. Raising the seek tolerance well remedy this... 0 disables tolerance.

##- Seek Threshold(Smart Seeking):

Adjusting seek threshold(percentage). threshold to which the current content can be played back before dismissing for the next queue. Ex. The content you select to play maybe near the end instead of loading two seconds of credits; PseudoTV Live will tune the next show automatically. 100% disables threshold.


#General Information:

##- Channel Sharing (Multi-Room):

For "Multi-Room", Select an instance of Kodi/PseudoTV Live that will act as your primary "server". Under PseudoTV Live's settings "Options" change the file location to a shared path. Client-side, install PseudoTV Live, Under PseudoTV Live's settings "Options" change the file location to a shared path. Enable "Client Mode" *Optional, PseudoTV can automatically detect client mode however, if you'd like to force the mode, select in options. *All instances of Kodi must be configured for sharing. ie. Shared/Mapped Drives and Central Database. You can configure channel lineups from any instance of PseudoTV Live, however only your "Server" will build/update channels. 

1. https://kodi.wiki/view/MySQL 
1. https://kodi.wiki/view/Path_substitution 

After creating channels you'll find a folder called "logos" in the same directory selected in settings. Place custom logos here!! They will override logos PseudoTV Live has found for you. The image must be *.png and is case sensitive to the channel name. ex. Channel "Foo Bar" search's for a matching logo "Foo Bar.png"

##Channel Ordering (Numbering):

### - Number Assignment:

For full control of channel numbering it's recommend users create "Custom" user-defined channels. Channels 1-999 are reserved to users, anything higher is reserved and auto assigned to pre-defined channels.
Pre-defined channels yield no control over numbering; numbers are auto assign by type (ranging from channels 1000-9999), using lowest available number by type.
Imported M3U's and "Recommend Services" auto assigned by a multiplier based on the amount of imports staring at 10000, then applying the imports channel number. For example importing two m3u's/services. Import one will start at 10000, the other 20000. EX. If you are importing a m3u that contains channel 4.1, and 11. They will appear as 10004.1 and 10011.

### - EPG Ordering:

####- - IPTV Simple Settings:

"only number by order" must be disbled if you'd like to respect the channel numbers assigned in PseudoTV Live.
*NOTE: PseudoTV Live automatically applies the optimal settings to IPTV Simple in-order to maximize the user experience.

####- - Kodi PVR & LiveTV Settings:
If you want the exact channel numbers from PseudoTV Live to reflect onscreen, you'll have to enable "Use channel order from backend". While in settings "Synchronize channel groups with backend" should also be enabled.
*NOTE: changes will require users to clear data from the same PVR settings menu


#Known Issues:

Multiple PVR backends supported; However, you must set "Client Priorities"  under Kodis "PVR & LiveTV" settings. Follow the directions below to clear guide data after setting priority.
Blank EPG cells; Kodi's EPG data is malformed; Enter Kodis "PVR & LiveTV" settings, navigate to "Guide" and click "Clear data".
Context Menu may be unavailable while viewing EPG.  To enable go do Kodis "PVR & LiveTV" then "Guide" and changing the default select action to "show context menu".
Some video sources (i.e. plugins, UPnP) do not support seeking, which could cause playback to fail. Try loading the content via Context Menu ("Play Programme","Play from here").
All content must include duration details either embedded into the file or via Kodi's Library.
Settings are dim and unselectable. Some settings require content to operate (ex. Selecting TV Networks require your library have TV Content). There are also actions that can not simultaneously run while PseudoTV background tasks are performed (ie. If you wait for tasks to finish, settings will become selectable). If you experience an error message and your settings are now unselectable. Either reboot Kodi, or disable/enable PseudoTV Live to temporarily fix, and be sure to report your error with a log.
Enable ", Channel surfing" Navigate Kodi's settings, find PVR Live TV settings and Playback then disabled confirm channel switches by pressing "ok".
