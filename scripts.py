__author__ = 'HO.OPOYEN'

from kivy.lang import Builder
from kivy.uix.codeinput import CodeInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, StringProperty, DictProperty, ObjectProperty
from kivy.factory import Factory

from conf import ENV

BANNER = """#Local Script Editor
#Available Globals are:
#   env: the current main window (Virtual Screen Manager) poiting to all widget
#   stack: current Stack
#   layout: current layout
#   tmpl_tree: Main Window Tree of Loaded template
#   file_selector: MainWindow File Selector
#   tmpls: Dict of registered template
#   ImgPack: ImagePack Class, for creating dynamic ones
#   os, os.path

"""

from collections import OrderedDict
from kivy.lang import Observable
from fields import Field

class Script(Field):
    name = 'SCRIPT'

    def __init__(self):
        Field.__init__(self)
        scriptList.register(self)

    def execute(self):
        pass


class BGScriptEditor(BoxLayout):
    modified = BooleanProperty(False)
    script_name = StringProperty('Untitled')
    env = ObjectProperty()

class REPL(CodeInput):
    locals = DictProperty()
    env = ObjectProperty()

    def on_env(self,*args):
        "Populate self.locals with important variable"
        env = self.env.__self__
        stack = env.ids.deck.stack
        if 'layout' in env.ids:
            layout = env.ids.layout.ids.page
        tmpl_tree = env.ids.deck.ids.tmpl_tree
        file_selector = env.ids.deck.ids.file_chooser
        from template import templateList as tmpls
        from models import ImgPack
        import os, os.path
        self.load_locals(locals())

    def load_locals(self, locals):
        self.locals.update(locals)

    def exec_code(self, code):
        try:
            exec code in self.locals
        except Exception,e:
            self.text+=str(e)
        else:
            self.text="Code executed without error"


Factory.register('REPL',REPL)

Builder.load_file('kv/scripts.kv')

#Now define the cache foundry for all templates
from kivy._event import EventDispatcher
from kivy.properties import *
from editors import *
class ScriptList(EventDispatcher):
    scripts = DictProperty()


    def copy(self):
        return self.scripts.copy()

    def __setitem__(self, key, value):
        #print 'registering template',key
        self.scripts[key] = value

    def __getitem__(self,name):
        #If the desired result is a file namee, reload it from file
        res = self.scripts[name]
        if isinstance(res, basestring):
            print ' i have to introduce autload relaod for script'
        return res

        return res

    def register(self,scr):
        self[scr.name] = scr

scriptList = ScriptList()

class Idle(Script):
    name = "IDLE"
    help = "Does nothing"

    tst_param = StringProperty('toto')
    num_param = NumericProperty(0)

    vars = {'tst_param': TextEditor, 'num_param': IntEditor}

    def execute(self):
        print 'idel executed'

class SplitMaker(Script):
    name = "SplitMaker"
    help = "Split selected image into X*Y sub images"
    num_col = NumericProperty(3)
    num_row = NumericProperty(3)

    vars = {'num_col' : AdvancedIntEditor,'num_row':AdvancedIntEditor}

    def execute(self):
        from conf import ENV, fill_env
        fill_env()
        from template import BGTemplate, templateList
        from fields import SubImageField
        from models import ImgPack
        #sub_tmpl = templateList.register(BGTemplate.FromField(SubImageField()))
        sub_tmpl_text='''
<SplitTMPL@BGTemplate>
#:import CARD conf.card_format
    size: CARD.size
    SubImageField:
        size: root.size
        id: default'''
        sub_tmpl = BGTemplate.FromText(sub_tmpl_text)
        templateList.register(sub_tmpl)
        print sub_tmpl.__class__
        try:
            img_path = ENV['file_selector'].selection[0]
        except Exception, E:
            from conf import alert
            alert('Select an image first')
            return

        W_ratio = 1.0/self.num_col
        H_ratio = 1.0/self.num_row
        for i in range(self.num_col):
            for j in range(self.num_row):
                values = dict()
                values['default.dimension'] = [img_path,i*W_ratio,j*H_ratio, W_ratio, H_ratio]
                pack = ImgPack(sub_tmpl, ENV['Qt'], ENV['Dual'], values)
                ENV['stack'].append(pack)

class MirrorBackground(Script):
    name = "Add Mirror Background"
    help = "Duplicate each entry as dual, optionnaly greyscale"
    grey_mode = BooleanProperty(False)

    vars = {'grey_mode' : BooleanEditor}

    def execute(self):
        from conf import ENV, fill_env
        fill_env()
        if self.grey_mode:
            print 'outch'
        for p in ENV['stack'][:]:
            pack = p.copy()
            pack.dual = True
            ENV['stack'].append(pack)


scripts = [x for x in globals().values() if type(x) == type(Script) and issubclass(x,Script) and x is not Script]
for s in scripts:
    scriptList.register(s())
