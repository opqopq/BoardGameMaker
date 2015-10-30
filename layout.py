"Define the layout maker/Editor with place holder only"
__author__ = 'opq'

from kivy.uix.floatlayout import FloatLayout
from kivy.base import Builder
from kivy.uix.scatter import Scatter
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, ListProperty
from kivy.metrics import cm
from kivy.uix.popup import Popup
from kivy.factory import Factory


class LayoutEditor(Popup):
    target = ObjectProperty()
    layout_maker = ObjectProperty()

from template import BGTemplate
class LayoutPlaceHolder(BGTemplate):
    index = NumericProperty()
    scale = 1
    layout_maker = ObjectProperty()

    def on_selected(self, instance, selected):
        BGTemplate.on_selected(self, instance, selected)

        if selected:
            if self.layout_maker.selected_ph and self.layout_maker.selected_ph is not self:
                self.layout_maker.selected_ph.selected=False
            self.layout_maker.selected_ph = self

        else:
            self.layout_maker.selected_ph = None

class BGLayoutMaker(FloatLayout):
    selected_ph = ObjectProperty(rebind=True, allownone = True)
    pages = ListProperty()
    page_index = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        FloatLayout.__init__(self, *args, **kwargs)
        self.pages.append(self.ids['page'])
        self.update_images()

    def update_images(self,*args):
        #Fill my pictures & bind to the stack
        from kivy.app import App
        from kivy.uix.image import Image
        stack = App.get_running_app().root.ids.deck.ids.stack
        pictures = self.ids.pictures
        pictures.clear_widgets()
        for s in stack.children:
            img = Factory.SelectableScreenshoot()
            img.lph = self
            img.texture = s.ids.img.texture
            img.tmpl = s.tmplWidget
            pictures.add_widget(img)
        stack.bind(children=self.update_images)

    def add_ph(self):
        from conf import card_format as CARD
        page = self.ids.page
        if self.selected_ph:
            self.selected_ph.selected = False
        page.index+=1
        ph = LayoutPlaceHolder(index=page.index, size= (CARD.width, CARD.height))
        ph.designed = True #trigger on designed
        ph.layout_maker = self
        page.add_widget(ph)
        self.selected_ph = ph
        ph.selected=True
        return ph

    def duplicate_ph(self):
        oph = self.selected_ph
        ph = self.add_ph()
        ph.size= oph.size
        ph.angle = oph.angle
        ph.selected = False
        for c in oph.children:
            print 'to dup', c
        ph.selected = True

    def remove_ph(self):
        if self.selected_ph:
            page = self.ids.page
            page.remove_widget(self.selected_ph)
            self.selected_ph = None

    def add_img_ph(self, object):
        ph = self.add_ph()
        from kivy.uix.image import Image
        if object.tmpl:
            img = object.tmpl
            img.designed = True
        else:
            img = Image(size=object.texture.size)
            img.texture = object.texture
        ph.size = img.size
        ph.add_widget(img)

    def rotate_ph(self, angle=90):
        if self.selected_ph:
            self.selected_ph.angle += angle

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
        return res

    def edit_ph(self):
        if self.selected_ph:
            p = LayoutEditor(target = self.selected_ph, title="Place Holder #%d Parameters"%self.selected_ph.index, layout_maker = self)
            p.open()

    def add_page(self):
        p = Factory.Page()
        self.ids.view.remove_widget(self.pages[-1])
        self.pages.append(p)
        self.ids.view.add_widget(p)
        self.ids['page'] = p
        self.page_index = len(self.pages) - 1
        self.ids.page_index.text = 'Page %d'%len(self.pages)
        return p

    def remove_page(self):
        if len(self.pages)>1:
            p = self.pages[self.page_index]
            self.ids.view.remove_widget(p)
            self.ids.view.add_widget(self.pages[max(self.page_index-1,0)])
            self.ids['page'] = self.pages[max(self.page_index-1,0)]
            del self.pages[self.page_index]

    def set_page(self, page_index):
        page_index = int(page_index.split()[-1])-1
        self.ids.view.remove_widget(self.pages[self.page_index])
        self.page_index = page_index
        self.ids.view.add_widget(self.pages[self.page_index])
        self.ids['page'] = self.pages[self.page_index]
        self.ids.page_index.text = 'Page %d'%(self.page_index+1)

    def add_mirror_page(self):
        p = self.add_page()
        res = [(child.pos, child.size, child.rotation) for child in self.ids.page.__self__.content.children]
        for p,s,r in res:
            ph = self.add_ph()
            ph.pos = self.width-p[0], p[1]
            ph.size = s
            ph.rotation = -r

    def clear_page(self):
        self.ids.page.clear_widgets()

Builder.load_file('kv/layout.kv')

