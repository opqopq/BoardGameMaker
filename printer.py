"""This module handle generation of formatted page, through several renderer: PIL, WX & Reportlab/PDF"""
#For Py2exe towork

import os,os.path
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty, DictProperty
from kivy.uix.carousel import Carousel
from kivy.metrics import cm
from kivy.lang import Builder
from kivy.vector import Vector
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm as r_cm

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
        print 'front page are all printer bbefore bakcpage. to be sorted out'
        fps, bps = stack
        #First determinez the number of item per page, acconirding to the dimensions
        x,y= Vector(fitting_size)/cm(1)
        NUM_COL = int((width-left)/(x+5/cm(1)))
        NUM_ROW = int((height-top-bottom)/(y+5/cm(1)))
        PICT_BY_SHEET=NUM_COL*NUM_ROW
        if not(fps) and not(bps):
            print 'Warning: nothing to print'
            return
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
                            src = fps.pop()
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
                            src = bps.pop()
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
        print 'settping on', item
        #Create tuple with qt * (source,dual)
        if not isinstance(item, Factory.get('StackPart')): continue
        if item.verso=='normal':#front
            deck_front += item.qt*[item.source]
        else:
            deck_back += item.qt*[item.source]
        print 'adding', item.source, item.qt, item.verso
        print 'back:', len(deck_back), 'front', len(deck_front)
    if deck_back and len(deck_front)!= len(deck_back):
        print 'WARNING: Front/Back discrepencies: ',len(deck_front), len(deck_back)

    def process(*args):
        book = PDFBook(dst)
        res = book.generate_pdf((deck_front,deck_back), fitting_size)
        if res:
            from os import startfile
            startfile(dst)
    from kivy.clock import Clock
    Clock.schedule_once(process, .3)
