import xbmc
import xbmcgui
import xbmcaddon

from resources.lib import foscam


__addon__   = xbmcaddon.Addon()
__id__ = __addon__.getAddonInfo('id')
__icon__  = __addon__.getAddonInfo('icon').decode("utf-8")
__version__ = __addon__.getAddonInfo('version')

addon_name = __addon__.getLocalizedString(32000)

INVALID_PASSWORD_CHARS = ('{', '}', ':', ';', '!', '?', '@', '\\', '/')
INVALID_USER_CHARS = ('@',)

#Get settings.xml data    
def getSettings(): 
    activeCameras = []
    motion_enabled = False
    sound_enabled = False
	
    for camera_number in '1234':
        log_verbose("Getting settings for Camera " + camera_number)
        if bool(get_setting('camera' + camera_number)):

            host = get_setting('host' + camera_number)
            port = get_setting('port' + camera_number)
            username = get_setting('username' + camera_number)
            password = get_setting('password' + camera_number)
            preview_enabled = get_setting('preview_enabled' + camera_number)

            alarm_trigger = get_setting('alarm_trigger' + camera_number).lower()
            if 'motion' in alarm_trigger:
                motion_enabled = True
            if 'sound' in alarm_trigger:
                sound_enabled = True

            check_interval = int(get_setting('check_interval' + camera_number))
            duration = float(get_setting('duration' + camera_number))
            location = get_setting('location' + camera_number).lower()
            scaling = float(get_setting('scaling' + camera_number))
            
            motion_sensitivity = int(get_setting('motion_sensitivity' + camera_number))
            motion_trigger_interval = int(get_setting('motion_trigger_interval' + camera_number))
            sound_sensitivity = int(get_setting('sound_sensitivity' + camera_number))
            sound_trigger_interval = int(get_setting('sound_trigger_interval' + camera_number))
            
            if motion_enabled and sound_enabled:
                trigger_interval = min(motion_trigger_interval, sound_trigger_interval)
            elif motion_enabled:
                trigger_interval = motion_trigger_interval
            elif sound_enabled:
                trigger_interval = sound_trigger_interval

            advanced_alarm_settings = bool(get_setting('advanced' + camera_number))
            
            configuredCorrectly = checkSettings(camera_number, host, port, username, password)
            if configuredCorrectly:                    
                activeCameras.append([camera_number, host, port, username, password, preview_enabled, 
                                      motion_enabled, motion_sensitivity, motion_trigger_interval,
                                      sound_enabled, sound_sensitivity, sound_trigger_interval,
                                      check_interval, duration, location, scaling, trigger_interval, advanced_alarm_settings])

    if len(activeCameras) > 0:
        return True, activeCameras

    return False, "No cameras configured"
#--

            
#Checking user inputted data and test camera connection         
def checkSettings(camera_number, host, port, username, password):
    camera_settings = [camera_number, host, port, username, password]
    
    if not host:
        log_error("No host specified for Camera " + camera_number)
        return False

    invalid = invalid_user_char(username)
    if invalid:
        log_error("Invalid character in user name for Camera " + camera_number + ": " + invalid)
        return False

    invalid = invalid_password_char(password)
    if invalid:
        log_error("Invalid character in password for Camera " + camera_number + ": " + invalid)
        return False

    log_verbose("Testing connection to Camera " + camera_number)
    with foscam.Camera(camera_settings) as camera:
        success, msg = camera.test()
            
    if not success:
        log_error(msg)
        return False

    log_normal("Successful connection to Camera " + camera_number)
    log_verbose(msg)
    return True



#settings.xml file
def get_setting(ident):
    return __addon__.getSetting(ident)

def set_setting(ident, value):
    __addon__.setSetting(ident, value)

def get_bool_setting(ident):
    return get_setting(ident) == "true"

def open_settings(callback=None):
    if callback is not None:
        callback()
    __addon__.openSettings()

def notify(msg, time=10000):
    xbmcgui.Dialog().notification(addon_name, msg, __icon__, '') #, time)

def addon_info(info):
    return __addon__.getAddonInfo(info)

def get_string(ident):
    return __addon__.getLocalizedString(ident)
#--




#Error Checking
def invalid_char(credential, chars, stringid, show_dialog):
    for char in chars:
        if char in credential:
            if show_dialog:
                xbmcgui.Dialog().ok(get_string(32000), get_string(stringid),
                                    " ", " ".join(chars))
            return char
    return False

def invalid_password_char(password, show_dialog=False):
    return invalid_char(password, INVALID_PASSWORD_CHARS, 32105, show_dialog)

def invalid_user_char(user, show_dialog=False):
    return invalid_char(user, INVALID_USER_CHARS, 32106, show_dialog)
#--

def error_dialog(msg):
    xbmcgui.Dialog().ok(get_string(32000), msg, " ", get_string(32102))
    open_settings()


#Log Levels
def log(message, level=xbmc.LOGNOTICE):
    xbmc.log("{0} v{1}: {2}".format(__id__, __version__, message), level=level)
       
def log_normal(message):
    if int(__addon__.getSetting('debug')) > 0:
        log(message)
    
def log_verbose(message):
    if int(__addon__.getSetting('debug')) == 2:
        log(message)
        
def log_error(message):
    log(message, xbmc.LOGERROR)        
#--
