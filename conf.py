__author__ = 'opq'
from os.path import isdir


gamepath = "C:\Users\mrs.opoyen\SkyDrive\\Games"
if not isdir(gamepath):
    gamepath = "../../../../OneDrive/Games"
if not isdir(gamepath):
    from kivy.logger import Logger
    Logger.warn('No Existing Game Path found')


USE_PROXY = True
USE_PROXY = False

from kivy.logger import Logger
if USE_PROXY:
    Logger.warn('Using Proxy')


from kivy.metrics import cm
from kivy.event import EventDispatcher
from kivy.lang import Observable
from kivy.properties import NumericProperty, StringProperty, ReferenceListProperty

class CardFormat(EventDispatcher):
    width = NumericProperty(cm(6.35))
    height = NumericProperty(cm(8.8))
    size = ReferenceListProperty(width, height)

card_format = CardFormat()


class PageFormat(EventDispatcher):
    width = NumericProperty(cm(21))
    height = NumericProperty(cm(29.7))
    left = NumericProperty(cm(.8))
    right = NumericProperty(cm(.8))
    bottom = NumericProperty(cm(1))
    top = NumericProperty(cm(1))

page_format = PageFormat()

#This cache will get a copy of last opened dir for each file browser to simplify history
dir_cache = dict()

#import watchdog.events
#watchdog.events.FileCreatedEvent

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
        app.root.log(text, stack)
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
        app.alert(text,status_color, keep)

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
    ENV['stack'] = root.ids.deck.stack
    if 'layout' in root.ids:
        ENV['layout'] = root.ids.layout.ids.page
    ENV['tmpl_tree'] = root.ids.deck.ids.tmpl_tree
    ENV['file_selector'] = root.ids.deck.ids.file_chooser
    ENV['Dual'] = root.ids.deck.ids.dual.active
    ENV['Qt'] = int(root.ids.deck.ids.qt.text)

from kivy.clock import Clock
Clock.schedule_once(fill_env,1)