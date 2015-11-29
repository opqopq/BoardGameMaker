from os.path import isdir
from sys import platform
from kivy.config import ConfigParser
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivy.metrics import cm
from kivy.properties import NumericProperty, ReferenceListProperty, BooleanProperty
from kivy.resources import resource_add_path


if platform.startswith('win'):
    fname = 'bgm.ini'
else:
    fname = 'bgm_home.ini'

CP = ConfigParser(name='BGM')
CP.read(fname)

gamepath = CP.get('Path', 'gamepath')
if not isdir(gamepath):
    Logger.warn('No Existing Game Path found')
    gamepath = None
else:
    resource_add_path(gamepath)

FORCE_FIT_FORMAT = CP.getboolean('Layout','force_fit_format')

def set_force_fit_format(force):
    CP.set('Layout','force_fit_format',int(force))
    CP.write()
    global FORCE_FIT_FORMAT
    FORCE_FIT_FORMAT = int(force)

def startup_tips(stop):
    CP.set('Startup','startup_tips',stop)
    CP.write()

USE_PROXY = CP.getboolean('Proxy', 'use_proxy')

if USE_PROXY:
    Logger.info('Using Proxy')

FILE_FILTER = ('.jpg','.png','.gif','.kv', '.csv', '.xlsx')

class CardFormat(EventDispatcher):
    width = NumericProperty(cm(CP.getfloat('Card', 'width')))
    height = NumericProperty(cm(CP.getfloat('Card', 'height')))
    size = ReferenceListProperty(width, height)
    keep_ratio = BooleanProperty(True)
    ratio = NumericProperty(6.5/8.8)

    def updateW(self, W, unit):
        if unit == 'px':
            self.width = float(W)
        else:
            self.width = float(W) * cm(1)
        if self.keep_ratio:
            self.height = self.width/self.ratio

    def updateH(self, H, unit):
        if unit == 'px':
            self.height = float(H)
        else:
            self.height = float(H) * cm(1)
        if self.keep_ratio:
            self.width = self.height * self.ratio

    def on_keep_ratio(self, instance, keep_ratio):
        if keep_ratio:
            self.ratio = self.width/self.height

card_format = CardFormat()


class PageFormat(EventDispatcher):
    width = NumericProperty(cm(CP.getfloat('Page', 'width')))
    height = NumericProperty(cm(CP.getfloat('Page', 'height')))
    left = NumericProperty(cm(CP.getfloat('Page', 'left')))
    right = NumericProperty(cm(CP.getfloat('Page', 'right')))
    bottom = NumericProperty(cm(CP.getfloat('Page', 'bottom')))
    top = NumericProperty(cm(CP.getfloat('Page', 'top')))

page_format = PageFormat()

ENV = dict()

def fill_env(*args):
    from kivy.app import App
    ENV['app'] = app = App.get_running_app()
    from utils import log, alert
    if not app:
        return
    root = app.root
    ENV['main'] = root
    for _id in root.ids:
        ENV[_id] = root.ids[_id]
    ENV['log'] = log
    ENV['alert'] = alert
    #from printer import prepare_pdf
    #ENV['prepare_pdf'] = prepare_pdf

from kivy.clock import Clock
Clock.schedule_once(fill_env,1)

def CreateConfigPanel():
    from kivy.uix.settings import SettingsWithTabbedPanel as Settings
    settings = Settings(name='Settings')
    settings.add_json_panel('BGM', CP, filename='params.json')
    settings.add_kivy_panel()
    return settings

#Path Handling functions

DirCache={'last':gamepath}

def set_last_dir(src,value):
    DirCache[src] = value
    DirCache['last']  = value

def get_last_dir(src=None):
    #print 'get_last_dir', src, src in DirCache, DirCache.keys(), src is None
    if src is None or not(src in DirCache):
        src = 'last'
    if not DirCache[src]:
        return '.'
    return DirCache[src]

