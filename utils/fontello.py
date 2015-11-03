__author__ = 'HO.OPOYEN'
#taken from FA 4.2 _variable.scss

FONTELLO = {
    'icon-EllipseField': u'\ue800',
    'icon-RectangleField': u'\ue801',
    'icon-users': u'\ue802',
    'icon-user': u'\ue803',
    'icon-child': u'\ue804',
    'icon-ImageField': u'\ue805',
    'icon-add': u'\ue806',
    'icon-unlink': u'\ue807',
    'icon-clock': u'\ue808',
    'icon-bookmark-empty': u'\ue809',
    'icon-SymbolField': u'\ue80a',
    'icon-SvgField': u'\ue80b',
    'icon-edit-1': u'\ue80c',
    'icon-print': u'\ue80d',
    'icon-trash': u'\ue80e',
    'icon-new': u'\ue80f',
    'icon-Copy': u'\ue810',
    'icon-CopyField': u'\ue810',
    'icon-csv': u'\ue811',
    'icon-svg': u'\ue812',
    'icon-Settings': u'\ue813',
    'icon-export': u'\ue814',
    'icon-resize-vertical': u'\ue815',
    'icon-resize-horizontal': u'\ue816',
    'icon-apply': u'\ue817',
    'icon-Left': u'\ue818',
    'icon-Right': u'\ue819',
    'icon-Top': u'\ue81a',
    'icon-Bottom': u'\ue81b',
    'icon-down': u'\ue81c',
    'icon-left': u'\ue81d',
    'icon-right': u'\ue81e',
    'icon-up': u'\ue81f',
    'icon-down-big': u'\ue820',
    'icon-left-big': u'\ue821',
    'icon-right-big': u'\ue822',
    'icon-up-big': u'\ue823',
    'icon-table': u'\ue824',
    'icon-SubImageField': u'\ue825',
    'icon-TemplateField': u'\ue826',
    'icon-list-alt': u'\ue827',
    'icon-book': u'\ue828',
    'icon-ajust': u'\ue829',
    'icon-save': u'\ue82a',
    'icon-console': u'\ue82b',
    'icon-ImgChoiceField': u'\ue82c',
    'icon-PolygonField': u'\ue82d',
    'icon-cubes': u'\ue82e',
    'icon-TransfoField': u'\ue82f',
    'icon-eyedropper': u'\ue830',
    'icon-brush': u'\ue831',
    'icon-WireField': u'\ue832',
    'icon-dribbble': u'\ue833',
    'icon-cancel': u'\ue834',
    'icon-ok': u'\ue835',
    'icon-link': u'\ue836',
    'icon-chart-line': u'\ue837',
    'icon-MeshField': u'\ue838',
    'icon-ColorChoiceField': u'\ue839',
    'icon-ColorField': u'\ue83a',
    'icon-db-shape': u'\ue83b',
    'icon-download-outline': u'\ue83c',
    'icon-folder-add': u'\ue83d',
    'icon-settings': u'\ue83e',
    'icon-duplicate': u'\ue83f',
    'icon-contrast': u'\ue840',
    'icon-waves': u'\ue841',
    'icon-TextField': u'\ue842',
    'icon-edit': u'\ue843',
    'icon-resize-full': u'\ue844',
    'icon-BezierField': u'\ue845',
    'icon-MaskField': u'\ue846',
    'icon-acrobat': u'\ue847',
    'icon-zoom-in': u'\ue848',
    'icon-zoom-out': u'\ue849',
    'icon-camera': u'\ue84a',
    'icon-EffectField': u'\ue84b',
    'icon-stumbleupon': u'\ue84c',
    'icon-layout-1': u'\ue84d',
    'icon-BorderField-old': u'\ue84e',
    'icon-Deck': u'\ue84f',
    'icon-resize-vertical-1': u'\ue850',
    'icon-resize-horizontal-1': u'\ue851',
    'icon-easel': u'\ue852',
    'icon-grid': u'\ue853',
    'icon-Browser': u'\ue854',
    'icon-Layout': u'\ue855',
    'icon-share': u'\ue856',
    'icon-script': u'\ue857',
    'icon-Designer': u'\ue858',
    'icon-cw': u'\ue859',
    'icon-ccw': u'\ue85a',
    'icon-BorderField':  u'\ue85b',
    'icon-terminal': u'\ue85c',
    'icon-saveas3': u'\ue85d',
    'icon-saveas2': u'\ue85e',
    'icon-library': u'\ue85f',
    'icon-saveas': u'\ue860',
}
from kivy.uix.label import Label
from kivy.properties import StringProperty

FONT_PATH = 'utils/fontello.ttf'


class FontIcon(Label):
    icon = StringProperty()

    def __init__(self,**kwargs):
        Label.__init__(self,**kwargs)
        self.font_name = FONT_PATH

    def on_icon(self,instance, icon):
        self.text = FONTELLO.get(icon, 'X') if icon.startswith('icon-') else FONTELLO.get('icon-'+icon, 'X')

if __name__ == '__main__':
    FONT_PATH = "fontello.ttf"
    from kivy.base import runTouchApp
    from kivy.uix.stacklayout import StackLayout
    s = StackLayout()
    for index,icon in enumerate(FONTELLO):
        i = FontIcon(icon = icon, color=(1,0,0,1),width=40, size_hint=(None, .15), font_size=15)
        print icon
        s.add_widget(i)
    runTouchApp(s)