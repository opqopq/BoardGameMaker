"Define the layout maker/Editor with place holder only"
__author__ = 'opq'

from kivy.uix.floatlayout import FloatLayout
from kivy.base import Builder
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.metrics import cm
from kivy.uix.popup import Popup

class LayoutEditor(Popup):
    target = ObjectProperty()
    layout_maker = ObjectProperty()

class LayoutPlaceHolder(Scatter):
    index = NumericProperty()
    selected = BooleanProperty()

    def on_touch_down(self, touch):
        self.selected = self.collide_point(*touch.pos)
        if self.selected:
            self.parent.parent.parent.selected_ph = self
        if touch.is_double_tap:
            self.parent.parent.parent.edit_ph()
        return Scatter.on_touch_down(self,touch)

class BGLayoutMaker(FloatLayout):
    selected_ph = ObjectProperty(rebind=True)

    def add_ph(self):
        from conf import card_format as CARD
        page = self.ids.page
        if self.selected_ph:
            self.selected_ph.selected = False
        page.index+=1
        ph = LayoutPlaceHolder(index=page.index, size= (CARD.width, CARD.height)
)
        page.add_widget(ph)
        self.selected_ph = ph

    def rotate_ph(self,angle=90):
        if self.selected_ph:
            self.selected_ph.rotation += angle

    def update_selected_ph(self,w, h, x, y, rotation):
        print "called with w:%s; h:%s; x:%s; y:%s; rotation:%s"%(w,h,x,y,rotation)
        if self.selected_ph:
            attrs={'width':w,'height':h,'x':x,'y':y, 'rotation': rotation}
            for name,src in attrs.iteritems():
                print 'Checking', name
                try:
                    _src = float(src)
                except Exception,E:
                    from conf import log
                    log("While changing Value %s: %s"%(name,E))
                    return
                #print 'Got value', _src, 'cm, changed to',
                #do multiply for rotation
                if name != 'rotation':
                    print 'multiply'
                    _src*=cm(1)
                #print _src, 'px'
                print 'former %s value'%name, getattr(self.selected_ph, name, None)
                print 'Setting %s to'%(name) , _src
                setattr(self.selected_ph,name,_src)
                print "new value", getattr(self.selected_ph, name, None)

    def export_phs(self):
        from kivy.vector import Vector
        res = [(Vector(child.pos)/cm(1), child.scale*Vector(child.size)/cm(1), child.rotation) for child in self.ids.page.__self__.content.children]
        #for child in self.ids.page.__self__.content.children:
        #    #print child, child.index, Vector(child.pos)/cm(1), child.scale*Vector(child.size)/cm(1), child.rotation, child.scale
        return res

    def edit_ph(self):
        if self.selected_ph:
            p = LayoutEditor(target = self.selected_ph, title = "Place Holder #%d Parameters"%self.selected_ph.index, layout_maker = self)
            p.open()

Builder.load_file('kv/layout.kv')

