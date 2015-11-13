__author__ = 'HO.OPOYEN'

from kivy.lang import Builder
from kivy.uix.codeinput import CodeInput
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from kivy._event import EventDispatcher
from kivy.properties import *
from editors import *
from sgm import StackPart
from conf import ENV, alert
from collections import OrderedDict
from kivy.lang import Observable
from fields import Field

BANNER = """#Available Globals are:
# root: Root Window
# stack: Current Stack
# StackPart: item of stack
# os, os.path
# alert & log: debug
# prepare_pdf()->test.pdf"""


class Script(Field):
    name = 'SCRIPT'
    def __init__(self):
        Field.__init__(self)
        scriptList.register(self)
        from kivy.app import App
        def inner(*args):
            self.stack = App.get_running_app().root.ids['deck'].ids['stack']
        from kivy.clock import Clock
        Clock.schedule_once(inner,1)

    def execute(self):
        pass

class FileScript(Script):
    source = StringProperty()
    vars = {'source': FileEditor}
    name = "File Loader"

    def execute(self):
        from conf import ENV, fill_env
        fill_env()
        if self.source:
            execfile(self.source, ENV)

class BGScriptEditor(BoxLayout):
    modified = BooleanProperty(False)
    env = ObjectProperty()
    locals = DictProperty()

    def exec_code(self, code):
        from kivy.factory import Factory
        rl = Factory.get('Repl_line')()
        try:
            exec code in self.locals
        except Exception,e:
            rl.mode = 'Err'
            rl.text = str(e)
        else:
            rl.mode = 'Out'
            rl.text = 'Execution done'
        self.ids.historic.add_widget(rl)

    def on_env(self,*args):
        "Populate self.locals with important variable"
        root = self.env.__self__
        stack = root.ids.deck.ids.stack
        #Filling the env
        import os, os.path
        from conf import alert, log
        from printer import prepare_pdf
        from conf import start_file
        self.load_locals(locals())

    def load_locals(self, locals):
        self.locals.update(locals)

Builder.load_file('kv/scripts.kv')

#Now define the cache foundry for all templates
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

    vars = {'tst_param': AdvancedTextEditor, 'num_param': IntEditor}

    def execute(self):
        print 'idel executed'

class SplitMaker(Script):
    name = "SplitMaker"
    help = "Split selected image into X*Y sub images"
    col = NumericProperty(3)
    row = NumericProperty(3)

    vars = {'col': AdvancedIntEditor, 'row':AdvancedIntEditor}

    def execute(self):
        if self.row == 0:
            self.row = 1
        if self.col == 0:
            self.col = 1
        stack = self.stack
        try:
            current_part = stack.last_selected
            if not current_part:
                raise ValueError()
        except Exception, E:
            from conf import alert
            alert('Select a Stack Item first')
            return

        pim = current_part.toPILImage()
        W_ratio = 1.0/self.col
        H_ratio = 1.0/self.row
        W,H = pim.size
        for i in range(self.col):
            for j in range(self.row):
                pack = StackPart()
                pack.qt = current_part.qt
                pack.dual = current_part.dual
                box = [i*W_ratio*W,j*H_ratio*H, (i+1)*W_ratio*W, (j+1)*H_ratio*H]
                pack.setImage(pim.crop([int(x) for x in box]))
                stack.add_widget(pack)

class MirrorBackground(Script):
    name = "Mirror Background"
    help = "Duplicate each entry as dual, optionnaly greyscale"
    greyscale = BooleanProperty(False)

    vars = {'greyscale' : BooleanEditor}

    def execute(self):
        stack = self.stack
        children = stack.children[::-1]
        if self.greyscale:
            from img_xfos import grey
        for p in children:
            if not isinstance(p,StackPart):
                continue
            pack = p.Copy()
            pack.dual = not p.dual
            if self.greyscale:
                pack.setImage(grey(pack.toPILImage()))
            stack.add_widget(pack)

class Flipper(Script):
    name = "Flip Image"
    help = "Flip H or V in place"
    vertical = BooleanProperty(False)
    horizontal = BooleanProperty(False)

    vars = {'vertical': BooleanEditor, 'horizontal': BooleanEditor}

    def execute(self):
        if not self.stack.last_selected:
            alert('Select a StackPart First')
            return
        img = self.stack.last_selected.toPILImage()
        if self.vertical:
            from img_xfos import v_flip
            img = v_flip(img)
        if self.horizontal:
            from img_xfos import h_flip
            img = h_flip(img)
        self.stack.last_selected.setImage(img)

class Rotater(Script):
    name = 'Rotate Image'
    help = 'Rotate current image in place'
    angle = NumericProperty(0)
    vars = {'angle': AdvancedIntEditor}

    def execute(self):
        if not self.stack.last_selected:
            alert('Select a StackPart First')
            return
        img = self.stack.last_selected.toPILImage()
        img = img.rotate(self.angle)
        self.stack.last_selected.setImage(img)

class GreyScale(Script):
    name = 'GreyScale'
    help = 'Turn Image to greyscale'

    def execute(self):
        if not self.stack.last_selected:
            alert('Selecta Stackpart First')
            return
        img = self.stack.last_selected.toPILImage()
        from img_xfos import grey
        self.stack.last_selected.setImage(grey(img))

scripts = [x for x in globals().values() if type(x) == type(Script) and issubclass(x, Script) and x is not Script]
for s in scripts:
    scriptList.register(s())
