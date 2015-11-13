"Define the layout maker/Editor with place holder only"
__author__ = 'opq'

from kivy.uix.floatlayout import FloatLayout
from kivy.base import Builder
from kivy.properties import NumericProperty, ObjectProperty, ListProperty, DictProperty, StringProperty, BooleanProperty
from kivy.factory import Factory
from fields import TextField

class BinCanNode:
    NUM_RETRY = 0

    def __init__(self,x,y,w,h):
        self.x, self.y, self.w, self.h = x,y,w,h
        self.used = False
        self.retry = dict()

    def __repr__(self):
        return '<BinLayout %s-%s:%sx%s>'%(self.x,self.y,self.w,self.h)

    def consume(self, w,h):
        self.used = True
        self.bottom = BinCanNode(self.x, self.y + h, self.w,self.h-h)
        self.right = BinCanNode(self.x+w, self.y, self.w-w, h)

    def find(self, ph, w= None, h = None, rotated = False):
        if w is None:
            w = ph.width if not rotated else ph.height
        if h is None:
            h = ph.height if not rotated else ph.width
        if self.used:
            return self.right.find(ph, w,h, rotated) or self.bottom.find(ph, w,h, rotated)
        elif w <= self.w and h <= self.h:
            self.consume(w, h)
            return self
        else:
            #This means If did not find any place. Retry with rotation ?
            if self.retry.get(ph,0) < self.NUM_RETRY:
                self.retry[ph] = self.retry.get(ph,0) + 1
                print 'Trying rotation for ', ph
                return self.find(ph,rotated = True)
            return None

class LayoutPlaceHolder(TextField):
    index = NumericProperty()
    layout_maker = ObjectProperty(rebind = True)

    def __repr__(self):
        return '<PH:#%s>'%self.index

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            self.selected = not(self.selected)
            #touch.ud['status'] = self.selected
        return TextField.on_touch_down(self, touch)

    def on_touch_move(self, touch):
        if self.selected:
            for c in self.layout_maker.selections:
                if c == self:
                    continue
                c.x += touch.dx
                c.y += touch.dy
            return TextField.on_touch_move(self, touch)
        return False

    def on_selected(self, instance, selected):
        if selected:
            self.layout_maker.selections[self] = None
            self.layout_maker.selected_ph = self
        else:
            del self.layout_maker.selections[self]
            self.layout_maker.selected_ph = False

class BGLayoutMaker(FloatLayout):
    selected_ph = ObjectProperty(rebind=True, allownone = True)
    pages = ListProperty()
    page_index = NumericProperty(0)
    selections = DictProperty()
    display_index = BooleanProperty(True, rebind = True)

    def on_display_index(self, instance, value):
        print 'ODI', instance, value

    def __init__(self, *args, **kwargs):
        FloatLayout.__init__(self, *args, **kwargs)
        p = Factory.Page()
        self.pages.append(p)
        self.ids.view.add_widget(p)
        self.update_images()

    def update_images(self,*args):
        #Fill my pictures & bind to the stack
        from kivy.app import App
        from kivy.uix.image import Image
        stack = App.get_running_app().root.ids.deck.ids.stack
        pictures = self.ids.pictures
        pictures.clear_widgets()
        a = Factory.SelectableAction()
        a.lph = self
        pictures.add_widget(a)
        for s in reversed(stack.children):
            for _ in range(s.qt):
                object = Factory.SelectableScreenshoot()
                object.stack = s
                object.lph = self
                object.texture = s.ids.img.texture
                #img.tmpl = s.tmplWidget
                #img.values = s.values
                #img.template = s.template
                pictures.add_widget(object)
        stack.bind(children=self.update_images)

    def add_all_imgs(self):
        for i,c in enumerate(reversed(self.ids.pictures.children)):
            #skip all
            if not i:
                continue
            self.add_img_ph(c)

    def add_ph(self):
        from conf import card_format as CARD
        page = self.pages[self.page_index]
        page.index += 1
        ph = LayoutPlaceHolder(index=page.index)
        ph.layout_maker = self
        ph.autofit = True
        ph.valign = 'middle'
        ph.halign='center'
        page.add_widget(ph)
        ph.designed = True
        return ph

    def duplicate_ph(self):
        from fields import BaseField
        from kivy.uix.image import Image
        oph = self.selected_ph
        s,a = oph.size, oph.rotation
        ph = self.add_ph()
        ph.size = s
        ph.rotation = a

    def remove_ph(self):
        if self.selected_ph:
            self.delete_ph(self.selected_ph)
            #remove myself from selection
            self.selected_ph.selected = False
            self.selected_ph = None

    def delete_ph(self,ph):
        page = ph.parent
        try:
            if ph.stack:
                from kivy.factory import Factory
                object = Factory.SelectableScreenshoot()
                object.stack = ph.stack
                object.lph = self
                object.texture = ph.stack.ids.img.texture
                self.ids.pictures.add_widget(object)
        except ReferenceError:
            print 'Warning: some mistake or is it a broken image ?'
        page.remove_widget(ph)

    def add_img_ph(self, object):
        if self.selected_ph:
            ph = self.selected_ph
        else:
            ph = self.add_ph()
        self.set_ph_img(ph, object, use_img_size=True)

    def set_ph_img(self, ph, object, use_img_size=False):
        #Remove object from list
        object.parent.remove_widget(object)
        ph.stack = object.stack
        if object.stack.image:#stack part with computed image
            if use_img_size:
                ph.size = object.stack.image.size
            ph.ids.img.texture = object.texture
        elif object.stack.tmplWidget or object.stack.template:
            self.ids.tmpltree.root.nodes = list()
            self.ids.tmpltree.clear_widgets()
            self.ids.tmpltree.tmplPath = ''
            self.ids.tmpltree.values = object.stack.values
            self.ids.tmpltree.tmplPath = object.stack.template
            img = self.ids.tmpltree.selected_node.template
            img.designed = True
            if use_img_size:
                ph.size = img.size
            else:
                img.size = ph.size
            def refresh(*args):
                img.pos = ph.pos
                img.size = ph.size
            ph.bind(size=refresh, pos=refresh)
            ph.add_widget(img)
            img.pos = ph.pos
        else:
            if use_img_size:
                ph.size = object.texture.size #now, bcause of size_hint 1
            from conf import FORCE_FIT_FORMAT, card_format
            if FORCE_FIT_FORMAT:
                ph.size = card_format.size
            ph.ids.img.texture = object.texture
        return ph

    def rotate_ph(self, angle=90):
        if self.selected_ph:
            self.selected_ph.angle += angle
            self.selected_ph.angle %= 360
            from template import BGTemplate
            if isinstance(self.selected_ph.children[0], BGTemplate):
                self.selected_ph.children[0].angle += angle
                self.selected_ph.children[0].angle %= 360

    def move_ph(self,direction):
        from conf import page_format
        if self.selected_ph:
            if direction == 'left':
                self.selected_ph.x = page_format.left
            elif direction == 'down':
                self.selected_ph.y = page_format.bottom
            elif direction == 'right':
                self.selected_ph.right = self.selected_ph.parent.width - page_format.right
            elif direction == 'up':
                self.selected_ph.top = self.selected_ph.parent.height - page_format.top

    def align_ph(self, direction):
        if self.selected_ph:
            way = {'x':'width','y':'height'}[direction]
            setattr(self.selected_ph, 'center_%s'%direction,getattr(self.selected_ph.parent,way)/2)

    def export_phs(self):
        for page in self.pages:
            for pindex, ph in enumerate(page.children):
                if not ph:
                    continue
                #Export layout
                if hasattr(ph, 'layout'):
                    ph.stack.layout = ph.layout
                elif ph.stack:
                    ph.stack.layout = ph.x, ph.y, ph.width, ph.height, ph.angle, pindex
                #For template, export values
                if ph.stack:
                    values = self.get_changes_values(ph)
                    if values:
                        ph.stack.values.update(values)
                    #In all case, proceed with realize: once linearized, stackpart has lost its preview
                    ph.stack.realise(withValue = True)

    def get_changes_values(self,ph):
        t = ph.children[0]
        from template import BGTemplate
        values = dict()
        if isinstance(t, BGTemplate):
            for c in t.ids:
                _child = getattr(t.ids,c)
                values[c] = getattr(_child,_child.default_attr)
                #print _child, _child.default_attr, getattr(_child,_child.default_attr)
            for c in t.vars:
                values[c] = getattr(t,c)
                #print 'Vars',c, getattr(t,c)
        return values

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
            for ph in sorted(p.children, key= lambda x:x.index):
                self.delete_ph(ph)
            self.ids.view.remove_widget(p)
            self.ids.view.add_widget(self.pages[max(self.page_index-1,0)])
            self.ids['page'] = self.pages[max(self.page_index-1,0)]
            del self.pages[self.page_index]
            self.ids.page_index.values = ['Page %d'%(i+1) for i in range(len(self.pages))]
            self.ids.page_index.text = 'Page %d'%len(self.pages)

    def set_page(self, page_index):
        page_index = int(page_index.split()[-1])-1
        self.ids.view.remove_widget(self.pages[self.page_index])
        self.page_index = page_index
        w = self.pages[self.page_index]
        self.ids.view.add_widget(w)
        self.ids['page'] = self.pages[self.page_index]
        self.ids.page_index.text = 'Page %d'%(self.page_index+1)

    def auto_fill_page(self, all=False):
        "Fill current page'PH with with images, in order"
        pictures = self.ids.pictures.children[:-1]
        phs = [x for x in self.pages[self.page_index].children]
        if not all:
            phs = [x for x in self.pages[self.page_index].children if not x.stack]
        for ph in phs:
            try:
                p = pictures.pop()
            except IndexError:
                break
            self.set_ph_img(ph,p, False)

    def move_page(self, page, new_index):
        print 'todo: move this mirror page to next the current one'
        #oindex = self.pages.index(page)
        #del self.pages[oindex]
        #self.pages.insert(new_index,page)
        #self.ids.page_index.values = ['Page %d'%x for x in range(len(self.pages))]

    def add_mirror_page(self):
        pi = self.page_index
        res = [(child.pos, child.size, child.angle) for child in self.pages[self.page_index].children]
        mp = self.add_page()
        self.move_page(mp,pi+1)
        from conf import page_format
        for p, s, r in reversed(res):
            ph = self.add_ph()
            ph.size = s
            ph.right = self.pages[self.page_index].width-p[0] - page_format.right
            ph.y = p[1]
            ph.angle = -r
            ph.layout = [ph.x,ph.y,ph.width,ph.height,ph.angle, self.page_index]
        return mp

    def apply_ph_dim(self):
        from kivy.metrics import cm
        if self.selected_ph:
            self.selected_ph.width = int(float(self.ids.ph_w.text) * cm(1))
            self.selected_ph.angle = int(self.ids.ph_angle.text)
            self.selected_ph.height = int(float(self.ids.ph_h.text) * cm(1))
            self.selected_ph.y = int(float(self.ids.ph_y.text) * cm(1))
            self.selected_ph.x = int(float(self.ids.ph_x.text) * cm(1))

    def clear_page(self):
        self.pages[self.page_index].clear_widgets()
        self.selections = dict()

    def align_group(self, way):
        if way.startswith('center'):
            mz = min([getattr(o, way[-1]) for o in self.selections])
            Mz = max([getattr(o, way[-1]) for o in self.selections])
            basis = int(mz + (Mz-mz)/2)
        else:
            if way in ['x','y']:
                op = min
            else:
                op = max
            basis = op([getattr(o, way) for o in self.selections])
        for s in self.selections:
            setattr(s, way, basis)

    def resize_group(self, dim):
        basis = max([getattr(c, dim) for c in self.selections])
        for x in self.selections:
            setattr(c, dim, basis)

    def distribute_group(self, dim):
        if len(self.selections) < 3:
            return
        sorted_phs = sorted(self.selections, key=lambda x: getattr(x,dim))
        m, M = getattr(sorted_phs[0], dim), getattr(sorted_phs[-1], dim)
        step = (M-m)/(len(self.selections)-1)
        for i, c in enumerate(sorted_phs):
            setattr(c, dim, m+i*step)

    def stick_group(self, way):
        a,b = self.selections
        _,Max = max((getattr(a,way),a), (getattr(b,way),b))
        _,Min = min((getattr(a,way),a), (getattr(b,way),b))
        if way == 'y':
            Max.y = Min.top
        else:
            Max.x = Min.right

    def group_selection(self, mode = True):
        children = self.pages[self.page_index].children
        for c in children:
            c.selected = mode

    def bin_pack(self):
        if not self.selections:
            return
        sorted_phs = sorted(self.selections, key=lambda x: (x.width*x.height, -x.index))
        from conf import page_format
        SIZE = page_format.width-page_format.left-page_format.right, page_format.height-page_format.top-page_format.bottom
        PAGE_LAYOUT= BinCanNode(0, 0, SIZE[0], SIZE[1])
        while sorted_phs:
            ph = sorted_phs.pop()
            layout = PAGE_LAYOUT.find(ph)
            if not layout:
                print 'WARNING: Could not fit: ', ph
            else:
                X,Y = layout.x, layout.y
                #Rebase properly
                ph.x = X+ page_format.left
                ph.top = page_format.height-page_format.top-Y
                ph.angle = layout.retry.get(ph,0) * 90
                ph.layout = [ph.x,ph.y,ph.width,ph.height,ph.angle, self.page_index]
                ##print 'Angle to be done'
                #'here, if angle is not null, I have to convert starting point to match pos'
                #from kivy.graphics.transformation import Matrix
                #m = Matrix()
                #m.rotate(ph.angle,0,0,1)

    def magic_fill(self):
        #alas, I have to linezarise in order to save layout for each widget
        from kivy.app import App
        App.get_running_app().root.ids.deck.linearize()

        init_pi = self.page_index
        from conf import page_format
        SIZE = page_format.width-page_format.left-page_format.right, page_format.height-page_format.top-page_format.bottom
        #first create tuple of fg/bg
        fg = list()
        bg = list()
        dual_dict = dict()
        for i,c in enumerate(reversed(self.ids.pictures.children)):
            if not i:
                continue
            if c.stack.dual:
                bg.append((c, i))
            else:
                fg.append((c, i))
        if fg and bg:
            if len(fg) != len(bg):
                print 'Warning: no same bnumber of BG/FG'
            dual = zip(fg, bg)
            for f, b in dual:
                f, i = f
                b, i = b
                dual_dict[f] = b
        #fill current page with what you can
        def skey(item):
            w,h = item[0].stack.getSize()
            return w*h, -item[1]
        self.ids.progress.max = len(fg)
        self.ids.progress.value = 1
        from kivy.clock import Clock
        def inner(*args):
            if not fg:
                Clock.unschedule(inner)
                from conf import alert
                alert('Book created')
                self.export_phs()
                from kivy.uix.widget import WidgetException
                try:
                    self.set_page("Page %d"%(init_pi+1))
                except WidgetException,Err:
                    print 'FATAL: Error in Setting page ???',Err
                return
            sorted_phs = sorted(fg, key=skey, reverse=True)
            added_ones = list()
            PAGE_LAYOUT = BinCanNode(0, 0, SIZE[0], SIZE[1])
            for f, i in sorted_phs:
                layout = PAGE_LAYOUT.find(f, *f.stack.getSize())
                if not layout:
                    continue
                del fg[fg.index((f, i))]
                added_ones.append(f)
                self.ids.progress.value += 1
                ph = self.add_ph()
                self.set_ph_img(ph, f, use_img_size= True)
                X, Y = layout.x, layout.y
                #Rebase properly
                ph.x = X + page_format.left
                ph.top = page_format.height-page_format.top-Y
                ph.angle = layout.retry.get(ph, 0) * 90
                ph.layout = [ph.x,ph.y,ph.width,ph.height,ph.angle, self.page_index]
            if not added_ones: #We could NOT feet any of the pictures: raise error:
                print 'Error: not pictures could be fit inside one page'
                from conf import alert
                alert('No more pictures can fit on page')
                Clock.unschedule(inner)
                return
            if dual_dict:
                #First page is done, create dual
                mp = self.add_mirror_page()
                for ph, b in zip (reversed(mp.children), [dual_dict[f] for f in added_ones]):
                    self.set_ph_img(ph,b, use_img_size= False) # Is it interesting: this will force that front & back have exact same size, depending on front size
            #Add a new page, only if necessay:
            if fg:
                self.add_page()
            #now loop on remaining fg/bg
            Clock.schedule_once(inner,.1)
        Clock.schedule_once(inner,.1)

    def new_book(self):
        self.pages = list()
        self.page_index = 0
        self.ids.view.clear_widgets()
        p = Factory.Page()
        self.pages.append(p)
        self.ids.view.add_widget(p)
        self.ids.page_index.values = ['Page 1']
        self.ids.page_index.text = 'Page %d'%len(self.pages)
        self.update_images()

Builder.load_file('kv/layout.kv')

