__author__ = 'HO.OPOYEN'

from IPython import start_ipython as si, get_ipython
from thread import start_new_thread
from main import BGMApp
from time import sleep

class DebugApp(BGMApp):
    def build(self):
        root = BGMApp.build(self)
        ip = get_ipython()
        ip.ex('app = App.get_running_app()')
        ip.ex('app.set_screen="designer"')
        from kivy.clock import Clock
        def loader(*args):
            ip.ex('designer = app.root.ids.designer')
            ip.ex('rs = app.root.ids.designer.ids.content')
        Clock.schedule_once(loader,1)
        sleep()
app = BGMApp()

#start ipython in thread, as kivy has to run in mainthread
tID = start_new_thread(si,())

CONTINUE = True
while CONTINUE:
    ip = get_ipython()
    if ip:
        CONTINUE = False
    sleep(0.1)
print 'IPYTHON', get_ipython()

ip.ex('from kivy.app import App')
ip.ex('app = App.get_running_app()')
#ip.ex('dekc = app.root.ids.deck')

app.run()
