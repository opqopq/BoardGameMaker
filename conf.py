__author__ = 'opq'
from os.path import isdir
from kivy.config import ConfigParser
from kivy.config import platform

if platform() == 'win': #work
    fname = 'bgm.ini'
else:
    fname = 'bgm_home.ini'

CP = ConfigParser(name='BGM')
CP.read(fname)

gamepath = CP.getdefault('Path', 'gamepath', r'C:\Users\mrs.opoyen\SkyDrive\Games')
if not isdir(gamepath):
    gamepath = "../../../../OneDrive/Games"
if not isdir(gamepath):
    from kivy.logger import Logger
    Logger.warn('No Existing Game Path found')
else:
    from kivy.resources import resource_add_path
    resource_add_path(gamepath)

USE_PROXY = CP.getboolean('Proxy', 'use_proxy')

from kivy.logger import Logger
if USE_PROXY:
    Logger.info('Using Proxy')


from kivy.metrics import cm
from kivy.event import EventDispatcher
from kivy.lang import Observable
from kivy.properties import NumericProperty, StringProperty, ReferenceListProperty

class CardFormat(EventDispatcher):
    width = NumericProperty(cm(CP.getfloat('Card', 'width')))
    height = NumericProperty(cm(CP.getfloat('Card', 'height')))
    size = ReferenceListProperty(width, height)

card_format = CardFormat()

class PageFormat(EventDispatcher):
    width = NumericProperty(cm(CP.getfloat('Page','width')))
    height = NumericProperty(cm(CP.getfloat('Page','height')))
    left = NumericProperty(cm(CP.getfloat('Page','left')))
    right = NumericProperty(cm(CP.getfloat('Page','right')))
    bottom = NumericProperty(cm(CP.getfloat('Page','bottom')))
    top = NumericProperty(cm(CP.getfloat('Page','top')))

page_format = PageFormat()

#This cache will get a copy of last opened dir for each file browser to simplify history
dir_cache = dict()


from kivy.properties import DictProperty
class BGMCache(Observable):
    folder= StringProperty('.')
    cache= DictProperty()
bgmcache = BGMCache()


#Some utility func
from kivy.app import App

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

def wait_cursor(value=None):
    if value is not None:
        App.get_running_app().root.wait_mode = bool(value)
    else:
        App.get_running_app().root.wait_mode = not(App.get_running_app().root.wait_mode)

def alert(text, status_color=(0,0,0,1), keep = False):
    app = App.get_running_app()
    if app:
        try:
            app.alert(text,status_color, keep)
        except AttributeError:
            print 'ALERT did not work. Reverting to print:'
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
    #ENV['stack'] = root.ids.deck.stack
    #if 'layout' in root.ids:
    #    ENV['layout'] = root.ids.layout.ids.page
    #ENV['tmpl_tree'] = root.ids.deck.ids.tmpl_tree
    #ENV['file_selector'] = root.ids.deck.ids.file_chooser
    #ENV['Dual'] = root.ids.deck.ids.dual.active
    #ENV['Qt'] = int(root.ids.deck.ids.qt.text)
    #ENV['alert'] = alert
    ENV['log'] = log
    from template import templateList
    ENV['tmpls'] = templateList
    ENV['DEFAULT_TEMPLATE'] = templateList['Default']
    from printer import prepare_pdf
    ENV['prepare_pdf'] = prepare_pdf
    from models import ImgPack
    ENV['ImgPack'] = ImgPack

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


DirCache={'last':'.'}

def set_last_dir(src,value):
    DirCache[src] = value
    DirCache['last']  = value

def get_last_dir(src=None):
    #print 'get_last_dir', src, src in DirCache, DirCache.keys()
    if src is None or not(src in DirCache):
        src = 'last'
    return DirCache[src]

