"""This module handle generation of formatted page, through several renderer: PIL, WX & Reportlab/PDF"""
#For Py2exe towork

import os,os.path
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty, DictProperty
from kivy.uix.carousel import Carousel
from kivy.metrics import cm
from kivy.lang import Builder
from kivy.vector import Vector
from conf import card_format, page_format
from kivy.uix.floatlayout import FloatLayout

from kivy.factory import Factory

from fpdf import FPDF, fpdf
from PIL import Image

#Monkey patching fpdf for Pillow
fpdf.Image = Image


Builder.load_file('kv/printer.kv')


class BGPrinter(FloatLayout):
    "BG Printer widget, displaying printpreview as caroussel"

class SheetLayout(Widget):
    Dual = BooleanProperty()
    number = NumericProperty()
    name = StringProperty()
    book = ObjectProperty()

class BookLayout(Carousel):
    stack = ObjectProperty()
    bag = DictProperty()

    def layout(self, stack= None):
        self.clear_widgets()
        if stack is None:
            stack = self.stack
        if stack:
            self.stack= stack
            #First calculte how many card by sheet we have
            cards_by_sheet = int((page_format.width-page_format.left-page_format.right)/card_format.width) * int((page_format.height-page_format.bottom-page_format.top)/card_format.height)
            cards = list()
            for piece in stack:
                cards.extend([piece]*piece.size)
                blank = piece.template.blank()
                blank.apply_values(piece.values)
                self.bag[id(piece)] = blank
            i=0
            for index in range(len(cards))[::cards_by_sheet]:
                i += 1
                sheet_layout = SheetLayout(number=i, name="from %s"%index, Dual = False, book=self)
                self.add_widget(sheet_layout)
                ssheet = sheet_layout.ids.ssheet
                ssheet.stack = self.stack
                for card,widget in zip(cards[index:index+cards_by_sheet],list(ssheet.walk(restrict=True))[1:]):
                    #Here I'm copying existing blank item, as they can not be duplicated/reparented
                    blank = card.template.blank()
                    blank.apply_values(card.values)
                    widget.add_widget(blank)
                    #Fill the placeholder
                    blank.size = widget.size

    def export_imgs(self,stack):
        if stack:
            self.stack = stack
        if self.bag:
            for pid in self.bag:
                self.bag[pid].export_to_image('build/%s.png'%pid, (1,1,1,0.1))
                #####self.bag[pid].export_to_png('buid/%s_B.png'%pid)
                #self.bag[pid].export_to_image('build/%s_W.png'%pid, (1,1,1,1))
        else:
            for p in self.stack:
                blank = p.template.blank()
                blank.apply_values(p.values)
                blank.export_to_image('build/%s.png'%id(p))
        book = PDFBook()
        book.generate_pdf(self.stack)

class Printer(Widget):
    "One page of print preview, as a X*Y imgholder widget"
    stack = ObjectProperty()

    def __init__(self,*args,**kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.auto_fill()

    def auto_fill(self, cf=None):
        self.clear_widgets()
        if cf is None:
            cf = card_format
        IMGPlaceHolder = Factory.get('IMGPlaceHolder')
        for index_h in range(int(round(((page_format.width-page_format.left-page_format.right)/card_format.width)))):
            for index_v in range(int(round(((page_format.height-page_format.top-page_format.bottom)/card_format.height)))):
                self.add_widget(IMGPlaceHolder(
                        pos = (page_format.left + index_h*cf.width,page_format.bottom+index_v*cf.height)
                ))

    def snapshot(self):
        from conf import alert
        alert('Snapshot saved as page_%s.png'%id(self))
        self.export_to_png('page_%s.png'%id(self))
        from conf import start_file
        start_file('page_%s.png'%id(self))

class PDFPlaceHolder:
    def __init__(self,pos,size,angle):
        self.pos = pos
        self.size = size
        self.angle = angle

class PDFPage:
    def __init__(self, dual = False):
        self.ph_per_page = 0
        self.phs=list()
        self.dual = dual

    @classmethod
    def fromFormat(cls,card_format= card_format, withDual = False):
        w,h = card_format.width, card_format.height
        W,H = page_format.width, page_format.height
        left = page_format.left
        right = page_format.right
        top = page_format.top
        bottom = page_format.bottom
        self = cls()
        res = dict()
        res['front']=self
        self.ph_per_page = int(W/w)*int(H/h)
        if withDual:
            dual = cls(dual = True)
            res['back']=dual
            dual.ph_per_page = self.ph_per_page
        for index_h in range(int(round((W-left-right)/w))):
            for index_v in range(int(round((H-bottom-top)/h))):
                self.phs.append(PDFPlaceHolder(
                    pos = (left+index_h*w, bottom+index_v*h),#here if dual, then change it
                    size = (w,h),
                    angle = 0
                    )
                )
                if withDual:
                    dual.phs.append(PDFPlaceHolder(
                        pos = (W-(1+index_h)*w-right,bottom+index_v*h),
                        size = (w,h),
                        angle = 0
                    )
                )
        return res

def center(x,y,w,h):
    return x+w/2, y+h/2

class PDFBook:
    def __init__(self):
        self.page_format = None
        self.stack = None
        self.pages = None
        self.pdf = FPDF(unit="cm")

    def generate_pdf(self, stack, pages=None, dst='test.pdf'):
        if not stack:
            from conf import alert
            alert('Stack is empty !')
            return
        from conf import alert, log
        try:
            self.pages = []
            self.stack = list()
            if stack:
                for piece in stack:
                    self.stack.extend([piece]*piece.size)
            cards = list()
            if pages is None: #Auto template is on
                self.page_format = PDFPage.fromFormat(withDual=self.containsDual())
            #Gather Front & Back Packs
            fps = [p for p in self.stack if not p.dual]
            bps = [p for p in self.stack if p.dual]
            front_pages=list()
            back_pages=list()
            for cardlist, mode, target_list in zip((fps,bps),(False,True),(front_pages,back_pages)):
                print 'loop:', "card list: %s"%cardlist, 'mode %s'%mode,"target_list : %s"%target_list
                if cardlist:
                    index = 0
                    pf = self.AddPage(mode, target_list)
                    while cardlist:
                        #print index, pf.ph_per_page
                        if index == pf.ph_per_page:
                            index = 0
                            pf = self.AddPage(mode, target_list)
                        item = cardlist.pop(0)
                        ph = pf.phs[index]
                        fname = 'build/%s.png'%(id(item))
                        phx,phy = Vector(ph.pos)/cm(1)
                        phw,phh = Vector(ph.size)/cm(1)
                        if ph.angle:
                            self.pdf.rotate(ph.angle,*center(phx,phy,phw,phh))
                        #print 'adding image to pdf %s'%fname, phx,phy, phw, phh
                        self.AddLines(phx,phy,phw,phh)
                        self.pdf.image(fname, phx,phy,phw,phh)
                        #self.pdf.image(fname, phx,phy,0,0)
                        if ph.angle:
                            self.rotate(0)
                        index+=1
            if len(front_pages) != len(back_pages) and len(back_pages):
                from conf import alert
                alert('Front & Back pages mismatch',(1,.3,1,.8), True)
            self.pdf.output(dst,'F')
            from conf import start_file
            start_file(dst)
        except Exception, e:
            alert(e)
            from traceback import format_exc
            log(e, format_exc())

    def containsDual(self):
        if self.stack:
            return any([x.dual for x in self.stack])

    def GetPageFormat(self, dual=False):
        if dual:
            return self.page_format['back']
        return self.page_format['front']

    def AddPage(self, mode, target_list):
        pf = self.GetPageFormat(mode)
        self.pdf.add_page()
        target_list.append(pf)
        return pf

    def AddLines(self, x, y, w, h):
        from kivy.metrics import cm
        step = 10.0/cm(1)
        pagging = 1.0/cm(1)
        self.pdf.line(x-step,y-pagging, x+w+step, y-pagging)
        self.pdf.line(x-pagging,y-step, x-pagging, y+h+step)
        self.pdf.line(x-step,y+h+pagging, x+w+step, y+h+pagging)
        self.pdf.line(x+w-pagging,y-step, x+w-pagging, y+h+step)


def prepare_pdf(stack, dst='test.pdf'):
    for p in stack:
        blank = p.template.blank()
        blank.apply_values(p.values)
        blank.export_to_image('build/%s.png'%id(p))
    def process(*args):
        book = PDFBook()
        book.generate_pdf(stack, dst=dst)
    from kivy.clock import Clock
    Clock.schedule_once(process, .3)