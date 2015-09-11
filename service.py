
import xbmc 
import xbmcvfs  
import xbmcaddon 
import time

from threading import Thread
from os import path

from resources.lib import foscam
from resources.lib import common
from resources.lib import gui

__addon__   = xbmcaddon.Addon()
__id__ = __addon__.getAddonInfo('id')

g_reset = False
    
class  Main:
    def __init__(self):
        common.log("Service is starting...") 
        self.path = xbmc.translatePath('special://profile/addon_data/%s' %__id__ ) 
       
        #Checks if directory exists for file storage, if not it creates it
        if not xbmcvfs.exists(self.path):
            try:
                xbmcvfs.mkdir(self.path)
            except:
                pass
            
        self._reset = False
        self.monitor = MyMonitor(action=self.restart)
        self.start()
            

    def restart(self):
        common.log_verbose("A setting change has been detected!")
        self._reset = True
        common.log_normal("Applying changed settings in 10 seconds")
        self.monitor.waitForAbort(10)
        self._reset = False
        self.start()
   
    def start(self):       
        #Collects camera configurations and confirm you can connect to at least 1   
        atLeastOneCamera, cameras = common.getSettings()
        common.log_verbose("Number of Cameras to start: " + str(len(cameras)))
        #cameras =
        #       camera_number[0], host[1], port[2], username[3], password[4], preview_enabled[5]
        #       motion_enabled[6], motion_sensitivity[7], motion_trigger_interval[8],
        #       sound_enabled[9], sound_sensitivity[10], sound_trigger_interval[11],
        #       check_interval[12], duration[13], location[14], scaling[15], trigger_interval[16], set_motion_settings[17]    

        if atLeastOneCamera:
            for camera in cameras:
                preview_enabled = camera[5]
                if preview_enabled:
                    atLeastOneCameraPreviewEnabled = True
                    break
                else:
                    camera_number = camera[0]
                    common.log_verbose("Preview disabled for Camera " + camera_number)
                      
        if atLeastOneCameraPreviewEnabled:
            for camera in cameras:
                camera_number = camera[0]
                preview_enabled = camera[5]
                set_motion_settings = camera[17]
                common.log_verbose(camera)
                
                if set_motion_settings:
                    self.configureAlarmSettings(camera)
                else:
                    self.resetCameraAlarmSettings(camera)

                if preview_enabled:
                    t = Thread(target=self.checkAlarm, args=(camera, self.path))
                    t.start()
                    common.log_verbose("Thread Started: Camera " + camera_number)
                
            common.log_normal("Cameras started")

        #Loop required to detect settings changes    
        while not self.monitor.abortRequested():
            self.monitor.waitForAbort(10)  

          

                
    #Camera Thread
    def checkAlarm(self, camera_settings, path):
        camera_number = camera_settings[0]
        motion_enabled = camera_settings[6]
        sound_enabled = camera_settings[9]
        duration = camera_settings[13]
        check_interval = camera_settings[12]
        trigger_interval = camera_settings[16]
        
        windowOpen = False

        #Send request to camera and receive response
        with foscam.Camera (camera_settings) as camera:
            snapshot_url = camera.snapshot_url
            preview = gui.CamWindow(camera_settings, path, snapshot_url)
            
            while not self.monitor.abortRequested() and not self._reset:
                alarmActive = False
                alarmState = camera.get_device_state()
                
                #Parses result for alarm state
                if alarmState:
                    for alarm, enabled in (('motionDetect', motion_enabled), ('sound', sound_enabled)):
                        if enabled:
                            param = "{0}Alarm".format(alarm)
                            #common.log_verbose("{0:s} = {1:d}".format(param, alarmState[param]))
                            if alarmState[param] == 2:
                                alarmActive = True
                                common.log_verbose("Alarm detected on Camera " + camera_number)
                                break                        

            
                if alarmActive:
                    durationTime = time.time() + duration   #Resets the time to close

                    if not windowOpen:
                        common.log_normal("Opening preview window for camera " + camera_number)
                        windowOpen = True
                        preview.start()

                else:
                    if windowOpen: #Alarm not active but window still open
                        common.log_verbose("Camera {0} window closing in {1} seconds.".format(camera_number, 1 - (time.time() - durationTime)))
                        if durationTime < time.time():
                            windowOpen = False
                            preview.stop()
                            common.log_verbose("Camera {0} window closed.  No alarm detected while window was still open.".format(camera_number))
                        
                #Wait for next loop logic      
                if alarmActive:
                    sleep = int(trigger_interval - 1)
                else:
                    sleep = int(check_interval)
                common.log_verbose("Camera {0} will sleep for {1} seconds".format(camera_number, sleep))
                self.monitor.waitForAbort(sleep)
               
    #--    
            

    #Configure Motion Settings
    def configureAlarmSettings(self, camera_settings):
         with foscam.Camera(camera_settings) as camera:
            # Applies new settings to camera

            camera_number = camera_settings[0]
            motion_enabled = camera_settings[6]
            sound_enabled = camera_settings[9]
            
            command = camera.set_motion_detect_config()
            common.log_verbose(command)
            if motion_enabled:
                command['isEnable'] = 1
                command['sensitivity'] = common.get_setting('motion_sensitivity' + camera_number)
                command['triggerInterval'] = common.get_setting('motion_trigger_interval' + camera_number)                                             
                self.send_command(command)
                common.log_verbose(command)
                
            command = camera.set_sound_detect_config()
            common.log_verbose(command)
            if sound_enabled:
                command['isEnable'] = 1
                command['sensitivity'] = common.get_setting('sound_sensitivity' + camera_number)
                command['triggerInterval'] = common.get_setting('sound_trigger_interval' + camera_number)
                #for iday in range(7):
                #    command['schedule{0:d}'.format(iday)] = 2**48 - 1
                self.send_command(command)
                common.log_verbose(command)


    def resetCameraAlarmSettings(self, camera_settings):
         with foscam.Camera(camera_settings) as camera:
            # Sets setting.xml settings based on camera settings

            camera_number = camera_settings[0]
            motion_enabled = camera_settings[6]
            sound_enabled = camera_settings[9]
            
            common.log_verbose('Resetting Camera Motion Config to settings.xml')
            response = camera.get_motion_detect_config()
            common.log_verbose(response)
            common.set_setting('motion_sensitivity' + camera_number, str(response['sensitivity']))
            common.set_setting('motion_trigger_interval' + camera_number, str(response['triggerInterval']))
                
            common.log_verbose('Resetting Camera Sound Config to settings.xml')
            response = camera.get_sound_detect_config()
            common.log_verbose(response)
            common.set_setting('sound_sensitivity' + camera_number, str(response['sensitivity']))
            common.set_setting('sound_trigger_interval' + camera_number, str(response['triggerInterval']))

    def send_command(self, command):
        response = command.send()
        if not response:
            msg = u"{0}: {1}".format(common.get_string(32104), response.message)
            common.notify(msg)  
    #--
        
class MyMonitor(xbmc.Monitor):
    def __init__(self, action):
        xbmc.Monitor.__init__(self)
        self.action = action
        
    def onSettingsChanged(self):
        self.action()
        
# Service Start        
if __name__ == '__main__':
    Main()

