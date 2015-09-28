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

    def save(self):
        try:
            self.pdf.save()
        except IOError:
            res= raw_input('Document is already opened. Close it first')
            self.pdf.save()

    def show(self):
        try:
            from os import startfile
            startfile(self.dst)
        except ImportError:
            print 'on a mac: no startfile !'

    def __init__(self, dst='test.pdf'):
        self.page_format = None
        self.stack = None
        self.pages = None
        self.pdf = Canvas(dst)
        self.dst = dst
        self.current_page_num = [0,0]
        self.current_face = 'F'
        self.index = list()
        self.x = 0
        self.y = 0

    def generation_step(self):
        "Will be called in order to show some advancement"

        i, row, col, face, item = self.index.pop()
        #print 'step on', i, row, col, face, item, self.current_face, self.current_page_num
        face_index = 0 if self.current_face=='F' else 1
        if self.current_face != face:
            self.current_face = face
            self.current_page_num[1-face_index] = i
            self.AddPage()
        elif self.current_page_num[face_index] != i:
            self.current_page_num[face_index] = i
            self.AddPage()

        #here we either get the source or convert to image
        if item.template:
            if item.tmplWidget:#it has been modified
                tmplWidget = item.tmplWidget
            else:
                from template import BGTemplate
                tmplWidget = BGTemplate.FromFile(item.template)
                if tmplWidget:
                    #only taking the last one
                    tmplWidget = tmplWidget[-1]
                else:
                    raise NameError('No such template: '+ item.template)
                print 'here to be added: adding on realizer, exporting & then removing. more tricky'
            if item.values:
                tmplWidget.apply_values(item.values)
            cim = tmplWidget.toImage()
            pim = frombuffer('RGBA', cim.size, cim._texture.pixels, 'raw', 'RGBA',0,1)
            src = ImageReader(pim)
            #src = ImageReader(pim.transpose(FLIP_TOP_BOTTOM))
        else:
            src = item.source

        if face == 'F':
            X,Y = col * self.x+ left, height-(1+row)*self.y - top
        else:
            X,Y = width -(1+col)*self.x-right, height-(1+row)*self.y - top
        self.pdf.drawImage(src, X*r_cm, Y*r_cm, self.x*r_cm, self.y*r_cm)
        #add line after image: they ll be above
        self.AddLines(X,Y,self.x,self.y)

    def calculate_size(self, stack, fitting_size):
        print 'in here, i souhld print to pdf some info, like deck name, date and num page'
        fps, bps = stack
        #First determinez the number of item per page, acconirding to the dimensions
        x,y= self.x, self.y = Vector(fitting_size)/cm(1)
        NUM_COL = int((width-left)/(x+5/cm(1)))
        NUM_ROW = int((height-top)/(y+5/cm(1)))
        PICT_BY_SHEET=NUM_COL*NUM_ROW
        if not(fps) and not(bps):
            print 'Warning: nothing to print: cancelling PDF generation'
            return

        if not NUM_COL or not NUM_ROW:
            PICT_BY_SHEET = 1
            if not NUM_ROW:
                NUM_ROW = 1
            if not NUM_COL:
                NUM_COL = 1
            x = self.x = width-left-right
            y = self.y = height-top-bottom

        if 0:
            print 'fitting size', fitting_size
            print "x,y", x,y
            print 'Num row', NUM_ROW
            print 'Num Col', NUM_COL
            print PICT_BY_SHEET , 'pictures by sheet'

        #Now prepare the whole list of index that will be used for the while loop

        index = self.index
        for i in range((len(fps)/PICT_BY_SHEET)+1):
                for row in range(NUM_ROW):
                    for col in range(NUM_COL):
                        try:
                            obj = fps.pop()
                            index.append((i,row,col,'F', obj))
                        except IndexError:
                            break
                for row in range(NUM_ROW):
                    for col in range(NUM_COL):
                        try:
                            obj = bps.pop()
                            index.append((i,row,col,'B', obj))
                        except IndexError:
                            break
        self.index.reverse()

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
    size = len(deck_back)+len(deck_front) # do that now, because they are going to be emptied
    book = PDFBook(dst)
    book.calculate_size((deck_front, deck_back), fitting_size)
    return (size , book)

#    def process(*args):
#        book = PDFBook(dst)
#        res = book.generate_pdf((deck_front,deck_back), fitting_size)
#        if res:
#            try:
#                from os import startfile
#                startfile(dst)
#            except ImportError:
#                print 'on a mac: no startfile !'
#    from kivy.clock import Clock
#    Clock.schedule_once(process, .3)
