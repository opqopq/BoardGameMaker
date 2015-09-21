"""This module handle generation of formatted page, through several renderer: PIL, WX & Reportlab/PDF"""
#For Py2exe towork

from kivy.metrics import cm
from kivy.vector import Vector
from kivy.factory import Factory

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm as r_cm
from reportlab.lib.utils import ImageReader
from PIL.Image import frombuffer, FLIP_TOP_BOTTOM

from conf import card_format
#Page Format - to be stuck into a .ini file
width = 21.0
height = 29.7
left = 0.8
right = 0.8
bottom = 1.0
top = 1.0

def center(x,y,w,h):
    return x+w/2, y+h/2

class PDFBook:
    def __init__(self, dst='test.pdf'):
        self.page_format = None
        self.stack = None
        self.pages = None
        self.pdf = Canvas(dst)
        self.dst = dst

    def generate_pdf(self, stack, fitting_size):
        print 'in here, i souhld print to pdf some info, like deck name, date and num page'
        fps, bps = stack
        #First determinez the number of item per page, acconirding to the dimensions
        x,y= Vector(fitting_size)/cm(1)
        NUM_COL = int((width-left)/(x+5/cm(1)))
        NUM_ROW = int((height-top-bottom)/(y+5/cm(1)))
        PICT_BY_SHEET=NUM_COL*NUM_ROW
        if not(fps) and not(bps):
            print 'Warning: nothing to print'
            return
        if 1:
            print 'fitting size', fitting_size
            print "x,y", x,y
            print 'Num row', NUM_ROW
            print 'Num Col', NUM_COL
            print PICT_BY_SHEET , 'pictures by sheet'

        for i in range((len(fps)/PICT_BY_SHEET)+1):
            #Add PAge if fps left
            if fps:
                for row in range(NUM_ROW):
                    for col in range(NUM_COL):
                        try:
                            item = fps.pop()
                            #here we either get the source or convert to image
                            if item.template:
                                if item.tmplWidget:#it has been modified
                                    tmplWidget = item.tmplWidget
                                else:
                                    print 'using basing template. with values ? ',
                                    from template import BGTemplate
                                    tmplWidget= BGTemplate.FromFile(item.template)
                                    if tmplWidget:
                                        #only taking the last one
                                        tmplWidget = tmplWidget[-1]
                                    else:
                                        raise NameError('No such template: '+ item.template)
                                    print 'this will not work: we need to force the creation of image somewhere to force creation of pixels'
                                    print 'here to be added: adding on realizer, exporting & then removing. more tricky'
                                if item.values:
                                    tmplWidget.apply_values(item.values)
                                cim = tmplWidget.toImage()
                                pim = frombuffer('RGBA',cim.size, cim._texture.pixels,'raw')
                                src = ImageReader(pim.transpose(FLIP_TOP_BOTTOM))
                            else:
                                src = item.source
                        except IndexError:
                            break
                        X,Y = col * x+ left, height-(1+row)*y - top
                        self.pdf.drawImage(src, X*r_cm, Y*r_cm, x*r_cm, y*r_cm)
                        #add line after image: they ll be above
                        self.AddLines(X,Y,x,y)
                self.AddPage()
            #Add Back page if bps left
            if bps:
                for row in range(NUM_ROW):
                    for col in range(NUM_COL):
                        try:
                            item = bps.pop()
                            #here we either get the source or convert to image
                            if item.template:
                                if item.tmplWidget:#it has been modified
                                    tmplWidget = item.tmplWidget
                                else:
                                    print 'using basing template. with values ? ',
                                    from template import BGTemplate
                                    tmplWidget= BGTemplate.FromFile(item.template)
                                    if tmplWidget:
                                        #only taking the last one
                                        tmplWidget = tmplWidget[-1]
                                    else:
                                        raise NameError('No such template: '+ item.template)
                                    if item.values:
                                        print 'yes', item.values
                                        tmplWidget.apply_values(item.values)
                                    else:
                                        print 'no'
                                    print 'this will not work: we need to force the creation of image somewhere to force creation of pixels'
                                    print 'here to be added: adding on realizer, exporting & then removing. more tricky'
                                cim = tmplWidget.toImage()
                                pim = frombuffer('RGBA',cim.size, cim._texture.pixels,'raw', 0,1)
                                src = ImageReader(pim.transpose(FLIP_TOP_BOTTOM))
                            else:
                                src = item.source
                        except IndexError:
                            break
                        X,Y = width -(1+col)*x-right, height-(1+row)*y - top
                        self.pdf.drawImage(src, X*r_cm, Y*r_cm, x*r_cm, y*r_cm)
                        #add line after image: they ll be above
                        self.AddLines(X,Y,x,y)
                self.AddPage()
        try:
            self.pdf.save()
        except IOError:
            res= raw_input('Document is already opened. Close it first')
            self.pdf.save()
        return True

    def AddPage(self):
        self.pdf.showPage()

    def AddLines(self, x, y, w, h):
        from kivy.metrics import cm
        step = 10.0/cm(1)
        pagging = 1.0/cm(1)
        self.pdf.lines([
            ((x-step)*r_cm, (y-pagging)*r_cm, (x+w+step)*r_cm, (y-pagging)*r_cm),
            ((x-pagging)*r_cm, (y-step)*r_cm, (x-pagging)*r_cm, (y+h+step)*r_cm),
            ((x-step)*r_cm, (y+h+pagging)*r_cm, (x+w+step)*r_cm, (y+h+pagging)*r_cm),
            ((x+w-pagging)*r_cm, (y-step)*r_cm, (x+w-pagging)*r_cm, (y+h+step)*r_cm)
        ])

def prepare_pdf(stack, fitting_size, dst='test.pdf'):
    #linearize stack to create list of element
    deck_front = list()
    deck_back = list()
    for item in stack.children:
        if not isinstance(item, Factory.get('StackPart')): continue
        #Create tuple with qt * (item) in front deck or back deck
        if item.verso=='normal':#front
            deck_front += item.qt*[item]
        else:
            deck_back += item.qt*[item]
    if deck_back and len(deck_front)!= len(deck_back):
        print 'WARNING: Front/Back discrepencies: ',len(deck_front), len(deck_back)

    def process(*args):
        book = PDFBook(dst)
        res = book.generate_pdf((deck_front,deck_back), fitting_size)
        if res:
            try:
                from os import startfile
                startfile(dst)
            except ImportError:
                print 'on a mac: no startfile !'
    from kivy.clock import Clock
    Clock.schedule_once(process, .3)
