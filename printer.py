"""This module handle generation of formatted page, through several renderer: PIL, WX & Reportlab/PDF"""
#For Py2exe towork

from kivy.metrics import cm
from kivy.vector import Vector
from kivy.factory import Factory

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm as r_cm
from reportlab.lib.utils import ImageReader
from PIL.Image import frombuffer, open as PILOpen


from conf import page_format
#Page Format - to be stuck into a .ini file
width = page_format.width/cm(1)
height = page_format.height/cm(1)
left = page_format.left/cm(1)
right = page_format.right/cm(1)
bottom = page_format.bottom/cm(1)
top = page_format.top/cm(1)

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
            from conf import start_file
            start_file(self.dst)
        except ImportError:
            print 'on a mac: no startfile !'

    def __init__(self, dst, mode, deck_front,deck_back):
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
        self.mode = mode
        self.banner = ""
        self.stack = (deck_front, deck_back)

    def generation_step(self, with_realize = False):
        "Will be called in order to show some advancement"
        i, row, col, face, item = self.index.pop()

        #Determine wheter a new page should be appended

        face_index = 0 if self.current_face == 'F' else 1
        if self.current_face != face:
            self.current_face = face
            self.current_page_num[1-face_index] = i
            self.AddPage()
        elif self.current_page_num[face_index] != i:
            self.current_page_num[face_index] = i
            self.AddPage()


        #Determine Image X/Y/W/H depending on print mode
        if self.mode == 'LAYOUT':
            x, y, self.x, self.y, angle, pageindex = item.layout
            x /= cm(1)
            y /= cm(1)
            self.x /= cm(1)
            self.y /= cm(1)
        elif self.mode == 'BINCAN':
            x, y, self.x, self.y, angle, item = item #hackick: replace item in place !
            x /= cm(1)
            y /= cm(1)
            self.x /= cm(1)
            self.y /= cm(1)
        else:
            if face == 'F':
                x, y = col * self.x + left, height-(1+row)*self.y - top
            else:
                #x, y = width - (1+col)*self.x - left - right, height-(1+row)*self.y - top
                x, y = width - (1+col)*self.x - right, height-(1+row)*self.y - top
            #self.x & slef.y has already been setp by calculate_size
            #Check is there is a layout that could be used, just for the angle
            if getattr(item, 'layout',0):
                angle = item.layout[4]
            else:
                angle = 0

        #Now that in item lies the Stack Item, before rendering it, inject special print vairables
        item.print_index = {
            'pagenum' : i,
            'stackrow': row,
            'stackcol': col,
            'pageface': face
        }

        # Now, define source for image: we either get the source or convert to image
        if item.image:#speicla case for complex image manip

            src = ImageReader(item.image.rotate(angle))
        elif item.template:
            if with_realize:
                item.realise(True,True)
                tmplWidget = item.tmplWidget
            elif item.tmplWidget:#it has been modified
                tmplWidget = item.tmplWidget
            else:
                from template import BGTemplate
                print '[Printer] Generation Step without tmplWidget'
                tmplWidget = BGTemplate.FromFile(item.template)
                if tmplWidget:
                    #only taking the last one
                    tmplWidget = tmplWidget[-1]
                else:
                    raise NameError('No such template: '+ item.template)
                print 'here to be added: adding on realizer, exporting & then removing. more tricky'
                if item.values:
                    tmplWidget.apply_values(item.values)
                from kivy.base import EventLoop
                EventLoop.idle()
            cim = tmplWidget.toImage(for_print=True)
            pim = frombuffer('RGBA', cim.size, cim._texture.pixels, 'raw', 'RGBA',0,1)
            src = ImageReader(pim.rotate(angle))
        else:
            src = item.source
            from conf import find_path
            src = find_path(src)
            if angle:
                src = ImageReader(PILOpen(src).rotate(angle))

        #print "Adding Image to pdf", i, row, col, face, item, src, x, y, self.x, self.y, angle
        self.pdf.drawImage(src, x*r_cm, y*r_cm, self.x*r_cm, self.y*r_cm, mask='auto')
        from conf import CP
        if CP.getboolean('Print','draw_cut_rect'):
            #add line after image: they ll be above
            self.AddLines(x,y,self.x,self.y)

    def calculate_size(self):
        from conf import alert
        alert('Calculating Size for mode %s'%self.mode)
        #Create all the necessary steps for while loop in printing
        #populate self.index with line made of i, row, col, face & item
        from datetime import date
        from os.path import split, relpath
        from conf import gamepath
        if self.dst.startswith(gamepath):
            title = relpath(self.dst, gamepath)
        else:
            title = split(self.dst)[-1]
        self.banner = "File: %s - Date : %s -  Print Mode: %s"%(title, date.today(), self.mode)
        if self.mode not in ('LAYOUT', 'BINCAN'):
            if self.mode == 'FORCED':
                from conf import card_format
                _w,_h = card_format.size
            else:
                _w,_h = self.mode
            ft = "%.2fcmx%.2fcm"%(_w/cm(1),_h/cm(1))
            self.banner += ' - Format : %s'%ft
        self.pdf.drawString(20,20, self.banner)
        fps, bps = self.stack
        #Swtich on Print Mode
        if self.mode == 'LAYOUT':
            dst = [(obj.layout[-1], 0, 0, 'F', obj) for obj in fps]
            dst.extend([(obj.layout[-1], 0, 0, 'F', obj) for obj in bps])
            self.index = sorted(dst, key=lambda x:x[0])
            self.index.reverse()
        elif self.mode == 'BINCAN':
            #######################################################
            from conf import page_format
            from layout import BinCanNode
            SIZE = page_format.width-page_format.left-page_format.right, page_format.height-page_format.top-page_format.bottom
            INDEX_PAGE = 0
            dual_dict = dict()
            fg = [(f,i) for (i,f) in enumerate(fps)]
            for f,b in zip(fps,bps):
                dual_dict[f]=b
            #fill current page with what you can
            def skey(item):
                w,h = item[0].getSize()
                return w*h, -item[1]
            fg = sorted(fg, key=skey, reverse=True)
            while fg:
                sorted_phs = fg[:]
                added_ones = list()
                PAGE_LAYOUT = BinCanNode(0, 0, SIZE[0], SIZE[1])
                for f, i in sorted_phs:
                    w,h = f.getSize()
                    layout = PAGE_LAYOUT.find(f, w,h)
                    if not layout:
                        continue
                    del fg[fg.index((f, i))]
                    X, Y = layout.x, layout.y
                    #Rebase properly
                    x = X + page_format.left
                    y = page_format.height-page_format.top-Y -h
                    angle = layout.retry.get(f, 0) * 90
                    self.index.append((INDEX_PAGE, 0, 0, 'F',(x, y, w, h, angle, f)))
                    added_ones.append((f, (x, y, w, h, angle)))
                if not added_ones: #We could NOT feet any of the pictures: raise error:
                    print 'Error: not all pictures could be fit inside one page'
                    break
                if dual_dict:
                    #First page is done, create dual
                    INDEX_PAGE += 1
                    for f,_layout in added_ones:
                        b = dual_dict[f]
                        x, y, w, h, angle = _layout
                        x = page_format.width - page_format.right -x - w
                        angle = -angle
                        self.index.append((INDEX_PAGE, 0, 0, 'F', (x, y, w, h, angle, b)))
                #Add a new page, only if necessay:
                if fg:
                    INDEX_PAGE+=1
            self.index.reverse()
            ######################################################
        else:
            if self.mode == 'FORCED':
                fitting_size = card_format.size
            else:
                fitting_size = self.mode
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
        self.pdf.drawString(20,30,self.banner)

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

def prepare_pdf(dst='test.pdf', stack= None, console_mode = True, mode = 'STANDARD'):
    if stack is None:
        from kivy.app import App
        stack = App.get_running_app().root.ids.deck.ids.stack
    #linearize stack to create list of element
    deck_front = list()
    deck_back = list()
    for item in stack.children:
        if not isinstance(item, Factory.get('StackPart')): continue
        #Create tuple with qt * (item) in front deck or back deck
        if item.verso == 'normal':#front
            deck_front += item.qt*[item]
        else:
            deck_back += item.qt*[item]
    if deck_back and len(deck_front)!= len(deck_back):
        print 'WARNING: Front/Back discrepencies: ',len(deck_front), len(deck_back)
    size = len(deck_back)+len(deck_front) # do that now, because they are going to be emptied
    book = PDFBook(dst, mode, deck_front, deck_back)
    book.calculate_size()
    if console_mode: # directly generate the stuff
        step_counter = range(size)
        while step_counter:
            print '-',
            step_counter.pop()
            book.generation_step(with_realize=True)
        book.save()
        book.show()
        from conf import alert
        alert('PDF Export completed')
        return False
    return (size , book)
