'Main Entry point for new KIVY bassed BGM'

todos = [
    'P3: change virtual screen stack',
    "P3: browser v2 - file & links",
    "P3: bug: when editing a template, then going back to deck & reediting the template, the panel switch is not done",
    "redo styles in designer switching to a popup with all style params",
    "when loading a deck, ensure taht kv file need not to be reloaded at each line: bummer: it does",
    "add custom klass import in designer ?????: when defining a klasss in kv or py it could nbe loaded in designer",
    "Bug: why laoding all templates from libray result in double load ? ",
    "P1: repair Z not working anymore",
    "Create a base parameter for template: all source will be read and save as realpath(base). If base is none, then base is the path of the template file once loaded",
    "when editing kv with forved fit, size change !!!!",
    "when printing, respect the same rule as layout: respect the size of template, of self.image. Use card.fitting size for pure image. When using forced fit, do this for all. Change layout to fit that",
    "bug: in between the 2 citites, when putting default.angle = 30 in csv files, it is NOT processed by import file",
    "auto layout bug: infinite loop between realise/inner and eventloopi lde",
    "learn way to split pdf other than pocket mod for bigger pictures",
    "add layout tools (distribute, stick,.... to designer. This means allows for multiple selection",
    "add a layout section editor in the edit of stackpart: at the bottom left for template. When editing that, this will issue value for layout"
]

for i, todo in enumerate(todos):
    print i, todo

from kivy.logger import Logger
Logger.setLevel('WARNING')

##############################################
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
        if not 'bgconsol' in self.ids:
            try:
                self.on_screen_name(self, 'Console', False)
            except ValueError:
                print '[LOG]: ',
                print text, stack
                return
        if not stack:
            import traceback
            stack = traceback.format_exc()
        from conf import alert
        alert(text)
        self.ids.bgconsole.add(text, stack)

from kivy.app import App
import cProfile

class BGMApp(App):
    title = "Board Game Maker"

    def build(self):
        from conf import CP, gamepath, path_reader
        import conf
        from kivy.clock import Clock
        root = RootWidget()
        if CP.getboolean('Startup','load_tmpl_lib'):
            root.ids.deck.load_template_lib(force_reload=True, background_mode=True)
        if CP.getboolean('Startup','startup_tips'):
            from kivy.factory import Factory
            p = Factory.StartupPopup()
            from kivy.clock import Clock
            def _inner(*args):
                p.open()
            Clock.schedule_once(_inner)

        if gamepath:
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
                    root.ids.deck.load_file(TARGET)
            Clock.schedule_once(launcher,1)
        return root

    def alert(self, text="", status_color=(0, 0, 0, 1), keep = False):
        button = self.root.ids.message
        bar = self.root.ids.message_bar
        bar.background_color = status_color
        button.text = str(text)
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
