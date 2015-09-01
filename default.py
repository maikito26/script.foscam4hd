import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os.path
from urllib import urlretrieve
#from PIL import Image
from threading import Thread
from resources.lib import common
from resources.lib import foscam


addon   = xbmcaddon.Addon()
addonid = addon.getAddonInfo('id')
addonname = addon.getAddonInfo('name')


ACTION_PREVIOUS_MENU = 10
ACTION_STOP = 13
ACTION_NAV_BACK = 92
ACTION_BACKSPACE = 110



class CamWindow(xbmcgui.WindowDialog):
    def __init__(self):
        path = xbmc.translatePath('special://profile/addon_data/%s' %addonid )
        loader = xbmc.translatePath('special://home/addons/%s/resources/media/loader.gif' %addonid )
        

        if not xbmcvfs.exists(path):
            try:
                xbmcvfs.mkdir(path)
            except:
                pass

        atLeastOneCamera, cameras = common.getSettings()

        #cameras =
        #       camera_number[0], host[1], port[2], username[3], password[4], preview_enable[5]
        #       motion_enabled[6], motion_sensitivity[7], motion_trigger_interval[8],
        #       sound_enabled[9], sound_sensitivity[10], sound_trigger_interval[11],
        #       check_interval[12], duration[13], location[14], scaling[15], trigger_interval[16], set_motion_settings[17]    

        if atLeastOneCamera:
            urls = []
            files = []
            for camera_settings in cameras:
                
                with foscam.Camera (camera_settings) as camera:
                    snapshot_url = camera.snapshot_url
                    
                    urls.append(snapshot_url)
                    files.append(os.path.join(path, camera_settings[0] + '.0.jpg'))


            coords = [      #Bottom Left X, Bottom Left Y, Width, Height
                (12, 12, 622, 342),
                (646, 12, 622, 342),
                (12, 366, 622, 342),
                (646, 366, 622, 342)
                ]

            imgs = []
            for c, f in zip(coords, files):
                # aspectRatio: integer - (values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
                img = xbmcgui.ControlImage(*c, filename=loader, aspectRatio = 0)
                self.addControl(img)            
                imgs.append(img)


            # workaround - superimposed image controls to prevent flicker
            imgs2 = []
            for c, f in zip(coords, files):
                img = xbmcgui.ControlImage(*c, filename='', aspectRatio = 0)
                self.addControl(img)            
                imgs2.append(img)
            

            cams = [list(l) for l in zip(urls, files, imgs, imgs2)]


            self.show()        
            self.isRunning = True


            for i, c in enumerate(cams):
                t = Thread(target=self.getImages, args=(i, c, path))
                t.start()


            while (not xbmc.abortRequested) and (self.isRunning):       
                xbmc.sleep(1000)   


            for i in xbmcvfs.listdir(path)[1]:
                if i <> "settings.xml":
                    xbmcvfs.delete(os.path.join(path, i))



    def getImages(self, i, c, path):
        x=0
        while (not xbmc.abortRequested) and (self.isRunning):
            try:
                x+=1
                c[1] = os.path.join(path, '%d.%d.jpg') %(i, x)
                urlretrieve(c[0], c[1])
                c[2].setColorDiffuse('0xFFFFFFFF')
                c[3].setColorDiffuse('0xFFFFFFFF')
                c[2].setImage(c[1], useCache=False)                
                xbmcvfs.delete(os.path.join(path, '%d.%d.jpg') %(i, x-1))
                c[3].setImage(c[1], useCache=False)               
            except Exception, e:
                xbmc.log(str(e))
                #error = xbmc.translatePath('special://home/addons/%s/resources/media/error.png' %addonid )
                #c[2].setImage(error, useCache=False)
                c[2].setColorDiffuse('0xC0FF0000')
                c[3].setColorDiffuse('0xC0FF0000')


    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_NAV_BACK, ACTION_BACKSPACE):
            self.isRunning = False
            self.close()

            

CW = CamWindow()
del CW

