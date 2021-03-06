'''Main Entry point for new KIVY bassed BGM'''

VERSION = 0, 2

todos = [
    'P3: change virtual screen stack...',
    "P3: browser v2 - file & links",
    "add custom klass import in designer ?????: when defining a klasss in kv or py it could nbe loaded in designer",
    "P1: fix SubTemplate Export KV: in here, it is the template content that is put in the KV, not the templat eitself",
    "Create a base parameter for template: all source will be read and save as realpath(base). If base is none, then base is the path of the template file once loaded",
    "when editing kv with forved fit, size change !!!!",
    "learn way to split pdf other than pocket mod for bigger pictures",
    "add a layout section editor in the edit of stackpart: at the bottom left for template. When editing that, this will issue value for layout",
    'P2: change font edit popup',
    "repair subimgafield",
    "how to record that a script has been pushed on an image? like splitter, or ",
    "add register function for field, script, template",
    'reintroduce package again with create package',
    'parameter from styles are not saved. ???',
]

for i, todo in enumerate(todos):
    print i, todo

from kivy.logger import Logger
#Logger.setLevel('WARNING')

##############################################
#Force load of FCTV
from kivy.garden.filechooserthumbview import FileChooserThumbView
##############################################

from utils import virtual_screen #to register VSMG
from kivy.lang import Builder
Builder.load_file('kv/bgm.kv')
##############################################
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class RootWidget(BoxLayout):

    screen_name = StringProperty('Deck')

    def on_screen_name(self, instance, name, set_screen=True):
        if not name in [s.name for s in self.ids.content.content]:
            if name == 'Browser':
                from geekbrowser import BGGeekBrowser
                self.ids['browser'] = last = BGGeekBrowser(name=name)
            elif name == 'Layout':
                from layout import BGLayoutMaker
                self.ids['layout'] = last = BGLayoutMaker(name=name)
            elif name == 'Console':
                from console import BGConsole
                self.ids['bgconsole'] = last = BGConsole(name=name, updated=False)
            elif name == 'Script':
                from scripts import BGScriptEditor
                self.ids['bgscript'] = last = BGScriptEditor(name=name, env=self)
            elif name == 'Designer':
                from designer import BGDesigner
                self.ids['designer'] = last = BGDesigner(name=name)
            elif name == 'Settings':
                from conf import CreateConfigPanel
                self.ids['settings'] = last = CreateConfigPanel()
            else:
                raise ValueError('No screen named %s' % name)
            self.ids.content.add_widget(last, name)
            last.name = name
        if set_screen:
            self.ids.content.set_screen(name)

    def log(self, text, stack=None):
        print 'printer of log, do i get an error ? ', text, stack
        if not 'bgconsole' in self.ids:
            try:
                self.on_screen_name(self, 'Console', False)
            except ValueError:
                from kivy.logger import Logger
                Logger.warn(text)
                print stack
                return
        if not stack:
            import traceback
            stack = traceback.format_exc()
        self.ids.bgconsole.add(text, stack)

from kivy.app import App

class BGMApp(App):
    title = "Board Game Maker"

    def load_file(self, window, filepath):
        if filepath.endswith('.kv'):
            self.set_screen('Designer')
            self.root.ids['designer'].load("@%s"%filepath)
        elif filepath.endswith('.xlsx'):
            self.set_screen('Deck')
            self.root.ids['deck'].load_file(filepath)
        elif filepath.endswith('.csv'):
            self.set_screen('Deck')
            self.root.ids['deck'].load_file_csv(filepath)


    def build(self):
        from conf import CP, gamepath
        from utils import path_reader
        root = RootWidget()
        if CP.getboolean('Startup', 'load_tmpl_lib'):
            root.ids.deck.load_template_lib(force_reload=True, background_mode=True)
        if CP.getboolean('Startup', 'startup_tips'):
            from kivy.factory import Factory
            p = Factory.StartupPopup()
            from kivy.clock import Clock
            def _inner(*args):
                p.open()
            Clock.schedule_once(_inner)
        if gamepath:
            from kivy.clock import Clock
            from time import clock
            #Startup file csv
            fpath = CP.get('Path','last_file')
            from os.path import join, isfile, split
            j = join(gamepath,fpath)
            TARGET= None
            if isfile(j):
                TARGET = join(gamepath,fpath)
            elif isfile(path_reader(fpath)):
                TARGET = path_reader(fpath)
            def launcher(*args):
                if TARGET:
                    root.ids.deck.load_folder(split(TARGET)[0])
                    if TARGET.endswith('.xlsx'):
                        root.ids.deck.load_file(TARGET)
                    elif TARGET.endswith('.csv'):
                        root.ids.deck.load_file_csv(TARGET)
            Clock.schedule_once(launcher,.2)
            #Filling ENV Global Variable
            from conf import fill_env
            Clock.schedule_once(fill_env, 1)

        #Dropfile Mngt
        from kivy.core.window import Window
        Window.bind(on_dropfile=self.load_file)


        return root

    def alert(self, text="", status_color=(0, 0, 0, 1), keep = False):
        button = self.root.ids.message
        bar = self.root.ids.message_bar
        bar.background_color = status_color
        button.text = str(text)
        from kivy.base import EventLoop
        EventLoop.idle()
        if not keep:
            from kivy.clock import Clock
            def cb(*args):
                self.alert(keep=True)
            Clock.schedule_once(cb, 2)

    def set_screen(self, screen_name):
        self.root.ids.screen_spinner.text = screen_name

    def compute_stats(self,grid):
        return self.root.ids['deck'].compute_stats(grid)

#    def on_start(self):
#        self.profile = cProfile.Profile()
#        self.profile.enable()

#    def on_stop(self):
#        self.profile.disable()
#        self.profile.dump_stats('bgm.profile')

if __name__ == '__main__':
    BGMApp().run()
