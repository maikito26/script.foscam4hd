
import os.path
import xbmc
import xbmcgui
import xbmcaddon
import common
import requests
import xbmcvfs
from urllib import urlretrieve
from threading import Thread

__addon__   = xbmcaddon.Addon()
__id__ = __addon__.getAddonInfo('id')

ACTION_PREVIOUS_MENU = 10
ACTION_BACKSPACE = 110
ACTION_NAV_BACK = 92
ACTION_STOP = 13
ACTION_SELECT_ITEM = 7

TEXTURE_FMT = os.path.join(__addon__.getAddonInfo('path'), 'resources', 'media', '{0}.png')

class Button(xbmcgui.ControlButton):
    WIDTH = HEIGHT = 32

    def __new__(cls, parent, action, x, y, scaling=1.0):
        focusTexture = TEXTURE_FMT.format(action + '-focus')
        noFocusTexture = TEXTURE_FMT.format(action)
        width = int(round(cls.WIDTH * scaling))
        height = int(round(cls.HEIGHT * scaling))
        self = super(Button, cls).__new__(cls, x, y, width, height, "", focusTexture, noFocusTexture)

        parent.buttons.append(self)
        return self

class CamWindow(xbmcgui.WindowDialog):
    def __init__(self, camera_settings, path, snapShotURL):        
        self.camera_number = camera_settings[0]
        scaling = camera_settings[15]
        position = camera_settings[14]
        self.path = path
        self.snapShotURL = snapShotURL
        self.setProperty('zorder', "99")
        self.buttons = []
      
        WIDTH = 320
        HEIGHT = 180

        width = int(float(WIDTH * scaling))
        height = int(float(HEIGHT * scaling))

        if "bottom" in position:
            y = 720 - height
        else:
            y = 0

        if "left" in position:
            x = 0
            start = - width
        else:
            x = 1280 - width
            start = width

        animations = [('WindowOpen', "effect=slide start={0:d} time=2000 tween=cubic easing=out".format(start)),
                      ('WindowClose', "effect=slide end={0:d} time=2000 tween=cubic easing=in".format(start))]
        
        self.img1 = []
        img = xbmcgui.ControlImage(x, y, width, height, '')
        self.addControl(img)
        img.setAnimations(animations)
        self.img1.append(img)

        self.img2 = []
        img = xbmcgui.ControlImage(x, y, width, height, '')
        self.addControl(img)
        img.setAnimations(animations)
        self.img2.append(img)

        button_scaling = 0.5 * scaling
        button_width = int(round(Button.WIDTH * button_scaling))
        self.close_button = Button(self, 'close', x + width - button_width - 10, y + 10, scaling=button_scaling)
        self.addControl(self.close_button)
        self.close_button.setAnimations(animations)

        common.log_verbose("Window Created for Camera " + self.camera_number)

    def start(self):
        self.isRunning = True
        self.show()
        t = Thread(target=self.getImages, args=())
        t.start()
        common.log_verbose("Thread Started to get Images for Camera " + self.camera_number)
        

    def getImages(self):
        monitor = xbmc.Monitor()
        x=0
        while (not monitor.abortRequested()) and (self.isRunning):
            try:
                x+=1
                filename = os.path.join(self.path, '%d.%d.jpg') %(int(self.camera_number), x)
                #common.log_verbose(filename)
                urlretrieve(self.snapShotURL, filename)
                self.img1[0].setImage(filename, useCache=False)
                self.img1[0].setColorDiffuse('0xFFFFFFFF')
                self.img2[0].setColorDiffuse('0xFFFFFFFF')
                xbmcvfs.delete(os.path.join(self.path, '%d.%d.jpg') %(int(self.camera_number), x-1))
                self.img2[0].setImage(filename, useCache=False)               
            except Exception, e:
                common.log(str(e))
                error = xbmc.translatePath('special://home/addons/%s/resources/media/error.png') %(__id__)
                self.img1[0].setImage(error, useCache=False)
                
        common.log_verbose("Thread Ended for Image Getting of Camera " + self.camera_number)
    

    def onControl(self, control):
        if control == self.close_button:
            common.log_verbose("Close Button pressed for Camera " + self.camera_number)
            self.stop()
            
    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK):
            common.log_verbose("Close Action pressed for Camera " + self.camera_number)
            self.stop()

    def stop(self):
        common.log_normal("Closing preview of Camera " + self.camera_number)
        self.isRunning = False
        self.close()

        
            
    
