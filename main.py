'Main Entry point for new KIVY bassed BGM'

todos= [
    'P3: change virtual screen stack',
    "P3: browser v2 - file & links",
    "P3: bug: when editing a template, then going back to deck & reediting the template, the panel switch is not done",
    "change stackpart selected to toggle button behavior",
    "hy does text editor appears when export liloops.kv",
    "redo styles in designer switching to a popup with all style params",
]

for i,todo in enumerate(todos):
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
            # elif name == 'PrintPreview':
            #     from printer import BGPrinter
            #     self.ids['printer'] = last = BGPrinter(name=name)
            elif name == 'Layout':
                from layout import BGLayoutMaker
                self.ids['layout'] = last = BGLayoutMaker(name=name)
#            elif name == 'Console':
#                from console import BGConsole
#                self.ids['bgconsole'] = last = BGConsole(name=name, updated=False)
#            elif name == 'Script':
#                from scripts import BGScriptEditor
#                self.ids['bgscript'] = last = BGScriptEditor(name=name, env=self)
            elif name == 'Designer':
                from designer import BGDesigner
                self.ids['designer'] = last = BGDesigner(name=name)
            elif name =='Settings':
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
                print 'Console/Log Screen disabled: resorting to print: ',
                print text, stack
                return
        if not stack:
            import traceback
            stack = traceback.format_exc()
        self.ids.bgconsole.add(text, stack)

from kivy.app import App

class BGMApp(App):
    title = "Board Game Maker"

    def build(self):
        from conf import CP, gamepath
        import conf
        if gamepath is None:
            conf.gamepath = '.'
            from kivy.clock import Clock
            def cb(*args):
                #self.set_screen('Settings')
                from kivy.uix.popup import Popup
                from kivy.uix.label import Label
                p=Popup(content=Label(text='Press escape then Please choose a valid Gamepath and reload BGM'),title='Choose Gamepath.')
                p.open()
            Clock.schedule_once(cb, 0)
            return conf.CreateConfigPanel()
        root = RootWidget()
        if CP.getboolean('Startup','load_tmpl_lib'):
            root.ids.deck.load_template_lib(force_reload=True, background_mode=True)
        return root

    def alert(self, text="", status_color=(0, 0, 0, 1), keep = False):
        button = self.root.ids.message
        bar = self.root.ids.message_bar
        bar.background_color = status_color
        button.text = str(text)
        if not keep:
            from kivy.clock import Clock
            def cb(*args):
                self.alert(keep = True)
            Clock.schedule_once(cb, 2)

    def set_screen(self, screen_name):
        self.root.ids.screen_spinner.text = screen_name

    def compute_stats(self,grid):
        return self.root.ids['deck'].compute_stats(grid)

if __name__ == '__main__':
    BGMApp().run()
