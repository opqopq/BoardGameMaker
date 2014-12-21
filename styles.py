"Contains all classes to managed styles, which are KV class added dynamicly to any fields"
__author__ = 'opq'




#Now define the cache foundry for all templates
from kivy._event import EventDispatcher
from kivy.properties import DictProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.lang import Builder

from editors import *

class Style(EventDispatcher):
    kvname = StringProperty()

class Border(Style):
    kvname = 'border'
    border_rgba = ListProperty([.2,1,.2,1])
    border_dash_offset = NumericProperty(3)
    border_dash_length = NumericProperty(5)
    border_width = NumericProperty(10)
    attrs = {'border_rgba': ColorEditor, 'border_dash_offset': AdvancedIntEditor,'border_dash_length': AdvancedIntEditor, 'border_width': AdvancedIntEditor}

class Shadow(Style):
    kvname = 'shadow'
    delta = NumericProperty(6)
    attrs = {'delta': AdvancedIntEditor}



class StyleList(EventDispatcher):
    styles = DictProperty()

    def copy(self):
        return self.styles.copy()

    def __setitem__(self, key, value):
        #print 'registering style',key
        self.styles[key] = value

    def __getitem__(self,name):
        #If the desired result is a file namee, reload it from file
        res = self.styles[name]
        return res

    def register(self,tmpl):
        self[tmpl.name] = tmpl

    def register_file(self, filename):
        #Remove any former trace of the file
        Builder.unload_file(filename)
        #Now create a widget
        try:
            Builder.load_file(filename)
            res = [x for x in Builder.rules if x[1].ctx.filename == filename]
        except Exception, E:
            from conf import log, alert
            import traceback
            alert(E)
            log(E,traceback.format_exc())
            res= list()
        for k,r in res:
            self[k.key] = k.key

styleList = StyleList()

styleList.register_file('kv/styles.kv')

def getStyle(stylename):
    res = [x for x in  globals().values()[:] if getattr(x,'kvname',"")==stylename]
    if res:
        return res[0]
    return None
