#Order of busines
# When unpacking a bgp file
# 1. read the content of the zip
# 2. find the py file if any. Execute it and find any Package instance yhere can be severals'
# 3. loop on all kv file, feeding them to any package insatnce found above
# 4. load all dek file, feeding them to any package instace found avbove

from kivy.logger import Logger

class Package:

    def __init__(self):
        self.files = set()
        from kivy.app import App
        self.bgm = App.get_running_app().ids.deck
        self.stack = self.bgm.ids.stack

    def deck_load(self, deck_path):
        Logger.info('Loading Deck File %'%deck_path)
        self.files.add(deck_path)

    def kv_load(self, kv_path):
        Logger.info('Loadinf KV File %s'%kv_path)
        self.files.add(kv_path)

    def save(self, path):
        #llop on all elements and change the necessary path
        pass

    @classmethod
    def fromfile(cls, path):
        p = Package()
        p.load(path)
        return p

    def load(self, path):
        from zipfile import ZipFile
        from imp import load_source
        zip = ZipFile(path)
        files = zip.filelist
        pyfs = [f for f in files if f.endswith('.py')]
        packages = set()
        for sf in pyfs:
            #exec them
            m = load_source(sf[:-3], sf)
            #find a package instance in them
            for obj in dir(sf):
                if isinstance(getattr(m, obj), Package):
                    packages.add(getattr(m, obj))

        kv_fs = [f for f in files if f.endswith('.kv')]
        for kv in kv_fs:
            from template import templateList
            templateList.register_file(kv)
            for package in packages:
                package.kv_load(kv)

        deckfs_csv = [f for f in files if f.endswith('.csv')]
        for deck in deckfs_csv:
            self.bgm.import_csv(deck)
            for package in packages:
                package.deck_load(deck)

        deckfs = [f for f in files if f.endswith('.xlsx')]
        for deck in deckfs:
            self.bgm.import_file(deck)
            for package in packages:
                package.deck_load(deck)

def register(package):
    if not isinstance(package, Package):
        raise ValueError('register only accept package instance')
    return 'toto'
