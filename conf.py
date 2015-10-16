from os.path import isdir
from kivy.config import ConfigParser
from sys import platform
from kivy.logger import Logger
from kivy.resources import resource_add_path
from kivy.metrics import cm
from kivy.event import EventDispatcher
from kivy.lang import Observable
from kivy.properties import NumericProperty, StringProperty, ReferenceListProperty, BooleanProperty, DictProperty
from kivy.app import App

if platform.startswith('win'):
    fname = 'bgm.ini'
else:
    fname = 'bgm_home.ini'

CP = ConfigParser(name='BGM')
CP.read(fname)

gamepath = CP.getdefault('Path', 'gamepath', r'C:\Users\mrs.opoyen\SkyDrive\Games')
if not isdir(gamepath):
    gamepath = "../../../../OneDrive/Games"
if not isdir(gamepath):
    Logger.warn('No Existing Game Path found')
else:
    resource_add_path(gamepath)


USE_PROXY = CP.getboolean('Proxy', 'use_proxy')

if USE_PROXY:
    Logger.info('Using Proxy')

FILE_FILTER = ('.jpg','.png','.gif','.kv', '.csv')

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

# This cache will get a copy of last opened dir for each file browser to simplify history
dir_cache = dict()


class BGMCache(Observable):
    folder = StringProperty('.')
    cache = DictProperty()

bgmcache = BGMCache()


def log(text, stack=None):
    app = App.get_running_app()
    if app:
        try:
            app.root.log(text, stack)
        except AttributeError:
            print 'WARNING: No Log function found; reverting to print'
            print '\t', text, stack
    else:
        print text, stack

def alert(text, status_color=(0,0,0,1), keep = False):
    app = App.get_running_app()
    if app:
        try:
            app.alert(text, status_color, keep)
        except AttributeError:
            print '\t', text, status_color, keep

def start_file(path):
    import os
    if hasattr(os, 'startfile'):
        os.startfile(path)
    else:
        os.system('open "%s"'%path)

ENV = dict()

def fill_env(*args):
    ENV['app'] = app = App.get_running_app()
    if not app:
        return
    root = app.root
    for _id in root.ids:
        ENV[_id] = root.ids[_id]
    ENV['log'] = log
    from template import templateList
    ENV['tmpls'] = templateList
    from printer import prepare_pdf
    ENV['prepare_pdf'] = prepare_pdf
    ENV['stack'] = root.ids['deck'].ids['stack']

from kivy.clock import Clock
Clock.schedule_once(fill_env,1)

def CreateConfigPanel():
    from kivy.uix.settings import SettingsWithTabbedPanel as Settings
    settings = Settings(name='Settings')
    settings.add_json_panel('BGM', CP, filename='params.json')
    settings.add_kivy_panel()
    return settings

#Path Handling functions

from os.path import normpath, join, split, sep
from kivy.resources import resource_add_path, resource_find

def path_reader(path):
    #normalize any path to be read according to the current OS
    not_sep = '/' if sep=='\\' else '\\'
    if sep in path:
        return normpath(path)
    else:
        return normpath(path.replace(not_sep,sep))

def find_path(path):
    from os.path import isfile
    if not isfile(path_reader(path)):
        if isfile(join(gamepath, path_reader(path))):
            return join(gamepath, path_reader(path))
        from conf import log
        log('Source does not exist at path %s'%(path))
    else:
        return path_reader(path)

DirCache={'last':gamepath}

def set_last_dir(src,value):
    DirCache[src] = value
    DirCache['last']  = value

def get_last_dir(src=None):
    #print 'get_last_dir', src, src in DirCache, DirCache.keys()
    if src is None or not(src in DirCache):
        src = 'last'
    return DirCache[src]

def toImage(self, bg_color=(1,1,1,0)):
    #create image widget with texture == to a snapshot of me
    from kivy.graphics import Canvas, Translate, Fbo, ClearColor, ClearBuffers, Scale
    from kivy.core.image import Image as CoreImage

    if self.parent is not None:
        canvas_parent_index = self.parent.canvas.indexof(self.canvas)
        self.parent.canvas.remove(self.canvas)

    fbo = Fbo(size=self.size, with_stencilbuffer=True)

    with fbo:
        ClearColor(*bg_color)
        ClearBuffers()
        Scale(1, -1, 1)
        Translate(-self.x, -self.y - self.height, 0)

    fbo.add(self.canvas)
    fbo.draw()
    from kivy.base import EventLoop
    #EventLoop.idle()
    cim = CoreImage(fbo.texture, filename = '%s.png'%id(self))

    fbo.remove(self.canvas)

    if self.parent is not None:
        self.parent.canvas.insert(canvas_parent_index, self.canvas)

    return cim
