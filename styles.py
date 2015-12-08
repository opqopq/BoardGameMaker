"Contains all classes to managed styles, which are KV class added dynamcaly to any fields"
__author__ = 'opq'

#Now define the cache foundry for all Templates
from kivy._event import EventDispatcher

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

class Cross(Style):
    kvname = 'cross'
    cross_color = ListProperty([1, 0, 0, 1])
    cross_width = NumericProperty(10)
    cross_dash_offset = NumericProperty(3)
    cross_dash_length =  NumericProperty(5)
    attrs = {'cross_color': ColorEditor, 'cross_dash_offset': AdvancedIntEditor,'cross_dash_length': AdvancedIntEditor, 'cross_width': AdvancedIntEditor}

class Shadow(Style):
    kvname = 'shadow'
    offset = NumericProperty(6)
    shadow_opacity = NumericProperty(.5)
    attrs = {'offset': AdvancedIntEditor, 'shadow_opacity': FloatEditor}


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
        self[tmpl.template_name] = tmpl

    def register_file(self, filename):
        #Remove any former trace of the file
        Builder.unload_file(filename)
        #Now create a widget
        try:
            Builder.load_file(filename)
            res = [x for x in Builder.rules if x[1].ctx.filename == filename]
        except Exception, E:
            from utils import alert
            from utils import log
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
