__author__ = 'HO.OPOYEN'

from kivy.uix.spinner import Spinner
from kivy.uix.behaviors import FocusBehavior

def find_char(char, names_list):
    for index, elt in enumerate(names_list):
        if elt.startswith(char):
            return index

class KeyboardSpinner(FocusBehavior, Spinner):

    def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'up':
            self.text = self.values[max(0,self.values.index(self.text)-1)]
        elif keycode[1] == 'down':
            self.text = self.values[min(self.values.index(self.text)+1, len(self.values)-1)]
        else:
            self.text = self.values[find_char(keycode[1], self.values) or self.values.index(self.text)]
        return True

from kivy.factory import Factory
Factory.register('KeyboardSpinner', KeyboardSpinner)