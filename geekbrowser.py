__author__ = 'HO.OPOYEN'

from urllib import quote, unquote
from kivy.uix.boxlayout import BoxLayout
from utils.proxy_urlrequest import UrlRequest
from conf import USE_PROXY, wait_cursor, log, alert
from kivy.properties import StringProperty, ListProperty
from kivy.lang import Builder
from xml.etree import cElementTree as ET
from kivy.uix.treeview import TreeViewLabel
from kivy.clock import  Clock
from urllib import urlretrieve
from bs4 import BeautifulSoup as BS

Builder.load_file('kv/geekbrowser.kv')

# Search URL for Game with a name
bgg_search_url = "http://www.boardgamegeek.com/xmlapi/search?search=%s"
# Search URL for Game with an ID
bgg_search_url_id = 'http://www.boardgamegeek.com/xmlapi2/thing?id=%s'
# Get Game Details
bgg_desc_url = "http://boardgamegeek.com/xmlapi/boardgame/%s"
# Standard Game page, to get the more infor stuff
bgg_complete_url = "http://boardgamegeek.com/boardgame/%s/%s"
# List of all images, pagged
#bgg_img_url = "http://www.boardgamegeek.com/geekimagemodule.php?action=imagemodule&objecttype=thing&objectid=%d&gallery=all&sort=recent&instanceid=10&showcount=30&rowsize=30&pageid=%d&ajax=1"
bgg_img_url = "http://www.boardgamegeek.com/geekimagemodule.php?action=imagemodule&objectid=%d&showcount=30&pageid=%d&ajax=1"
bgg_file_url = "http://boardgamegeek.com/geekfile.php?objecttype=thing&objectid=%d&pageid=%d&action=module&ajax=1&showcount=30&rowsize=30"
bgg_link_url = "http://boardgamegeek.com/geekitem.php?objectid=%d&subtype=boardgame&pageid=%d&view=weblinks&modulename=weblinks&showcount=30&action=linkeditems&ajax=1"

GAME_CACHE={}


def img_download(url, Widget, *args):
    from os.path import isfile, join
    fname = url.split('/')[-1]
    dst = join('cache',fname)
    if isfile('cache/%s'%fname):
        Widget.source = dst
        return
    if not USE_PROXY:
            Widget.source = url
            return
    def getter(*args):
        print 'urlretrieve', url, dst
        urlretrieve(url, dst)
        Widget.source = dst
    Clock.schedule_once(getter)

class BGGeekBrowser(BoxLayout):
    selected_game = StringProperty()

    images = ListProperty()
    files = ListProperty()
    links = ListProperty()

    def search_game(self, name):
        "Search a game. Callback to insert_games"
        self.ids.results.root_options={'text':'Results: %s'%name}
        url = bgg_search_url
        try:
            int(name)
            # if it is working, then it is an id
            url = bgg_search_url_id
        except ValueError:
            pass
        target=url%quote(name)
        ##wait_cursor(value=True)
        req = UrlRequest(target, on_success=self.insert_games, on_error=self.cb, on_failure=self.cb, on_redirect=self.cb, use_proxy=USE_PROXY)

    def cb(self, *args):
        print args
        #alert(str(args))
        #log(args)

    def insert_games(self, req, result):
        "Asynch. Insert Search Results in a tree"
        self.ids.results.clear_widgets()
        xml = ET.fromstring(unicode(result).encode('utf-8'))
        ##wait_cursor(False)
        bgs=xml.findall('boardgame')
        isID=False
        if not bgs:
            bgs=xml.findall('item')
            isID=True
        for index,bg in enumerate(bgs):
            #print index, bg, bg.tag, bg.text, bg.attrib, bg.keys(), bg.tail,
            try:
                game, name, year = bg.iter()
            except ValueError:
                game,name = bg.iter()
            tvl = TreeViewLabel(text = "%s (%s)"%(name.text, year.text))
            tvl.gid = game.attrib['objectid']
            tvl.name = name.text
            self.ids.results.add_node(tvl)
        self.ids.status.text = 'Found %d result(s) for %s'%(len(bgs),self.ids.search_field.text)
        if len(bgs) == 1:#only one result=>select item
            self.selected_game = tvl.gid

    def details_cb(self, req, result):
        "Build XML Tree from source"
        xml = ET.fromstring(unicode(result).encode('utf-8'))
        GAME_CACHE[req.gid] = xml
        self.insert_details(xml)

    def insert_details(self, xml):
        "Asynchorneously fill the game details widget with result from an XML/HTML source"
        ##wait_cursor(False)
        IS = self.ids.details
        res = xml.find("boardgame")
        IS.ids.nb_user.text = "%s - %s"%(res.find('minplayers').text, res.find('maxplayers').text)
        IS.ids.duration.text = "%s mns"%(res.find('playingtime').text)
        IS.ids.minimum_age.text = "%s years+"%(res.find('age').text)
        IS.ids.description.text = unquote(res.find('description').text).replace('<br/>','\n')
        img_download('http:'+res.find('thumbnail').text,IS.ids.thumbnail)
        #img_download('http:'+res.find('image').text,IS.ids.thumbnail)

    def game_details(self, tree, node):
        "Display/Hide degtails for a game selected in search result tree"
        if not hasattr(node, 'gid'):
            return
        gameID = self.selected_game = node.gid
        IS = self.ids.details
        IS.title = node.name
        if gameID in GAME_CACHE:
            self.insert_details(GAME_CACHE[gameID])
        else:
            url = bgg_desc_url%gameID
            req = UrlRequest(url, on_success=self.details_cb, use_proxy= USE_PROXY)
            req.gid = gameID
        #Now, get how many image, ilnk & files there are
        for url in [bgg_img_url, bgg_file_url, bgg_link_url]:
            req = UrlRequest(url%(int(self.selected_game),1), on_success=self.prepare_game_info,use_proxy=USE_PROXY)
            req._init_url = url
        #Now Get the More Information stuff
        #Plug a counter
        from kivy.uix.image import Image
        info = self.ids.details.ids.information
        wait = Image(center=(info.x + info.parent.center_x, info.y), source='img/image-loading.gif')
        info.add_widget(wait)
        info.wait = wait
        r=UrlRequest(bgg_complete_url%(gameID,quote(IS.title.lower().replace(' ','-'))), on_success=self.get_more_info, on_error=self.cancel_more_info, on_failure=self.cancel_more_info, use_proxy=USE_PROXY, timeout=7)

    def get_more_info(self,req,result):
        bs = BS(result)
        info = self.ids.details.ids.information
        info.text= bs.find(id="module_7").div.get_text()
        info.remove_widget(info.wait)

    def cancel_more_info(self, *args):
        info = self.ids.details.ids.information
        info.text= 'More Information'
        info.remove_widget(info.wait)

    def prepare_game_info(self,req,result):
        url = req._init_url
        TYPE = 'IMG'
        if url == bgg_link_url:
            TYPE = 'LINK'
        elif url == bgg_file_url:
            TYPE = 'FILE'
        target = self.ids.details.ids['nb_%s_page'%TYPE.lower()]
        bs = BS(result)
        try:
            total=int(bs.findAll('div',{"class":'pages'})[0].contents[0].split('of ')[-1])
        except:
            try:
                #Pure hack to compensate the facct the html for links are differents
                txt=bs.findAll('div',{"class":'pages'})[0].contents[0].split('of ')[-1].strip()
                total=int(txt.split(';')[-1])
            except ValueError:
                #print 'Issue with', txt.split(';')[-1]
                total=1
        #print 'There are %d pages for %s'%(total, TYPE)
        target.text = "%d Page(s)"%total
        if TYPE == 'IMG':
            for pageId in range(total):
                url = bgg_img_url%(int(self.selected_game),pageId+1)
                UrlRequest(url, self.get_images_urls, use_proxy=USE_PROXY)

    def get_images_urls(self,req, result):
        bs = BS(result)
        imgs=[x.get('src') for x in bs.findAll('img',{"class":None})]
        for index,img in enumerate(imgs):
            href=img.replace('_mt.jpg' , '.jpg')
            img="http:" + img.replace('_mt.jpg' , '_t.jpg')
            href = "http:" + href
            self.images.append((img,href))

    def prepare_gallery(self):
        title = self.ids.details.title
        #Check if a game folder exist, to prepare for img download
        from conf import gamepath
        from os.path import join, isdir
        path=join(gamepath,title)
        if not isdir(path):
            path = '.'
        line ="<option data-img-src='%(img)s' value='%(href)s'>  %(href)s</option>"
        tmpl ="""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
              <title>Gallery for %(gameName)s</title>
              <link rel="stylesheet" type="text/css" href="http://rvera.github.io/image-picker/css/bootstrap.css">
              <link rel="stylesheet" type="text/css" href="http://rvera.github.io/image-picker/css/bootstrap-responsive.css">
              <link rel="stylesheet" type="text/css" href="http://rvera.github.io/image-picker/examples.css">
              <link rel="stylesheet" type="text/css" href="http://rvera.github.io/image-picker/image-picker/image-picker.css">
              <script src="http://rvera.github.io/image-picker/js/jquery.min.js" type="text/javascript"></script>
              <script src="http://rvera.github.io/image-picker/image-picker/image-picker.js" type="text/javascript"></script>
        </head>
        <body style="font-size:62.5%%;">
                <base href="http://boardgamegeek.com/boardgame/%(gameId)s">
                <h2>Gallery for %(gameName)s</h2>
                <h3> Info Page for game <a href="http://boardgamegeek.com/boardgame/%(gameId)s">%(gameName)s #%(gameId)s</a></h2>
                <br/><br/><br/>
                    <p class='highlight'> It turns a select element into a more user friendly interface, e.g.: </p>
                <div class="alert">
                  <strong>Note: Chrome ONLY</strong> Image Picker: select and click download.
                </div>

                <form>
                <div id="accordion">
                    <h3><a href="#">Images</a></h3>
                        <div id="ImageGallery">
                            <div class="picker">
                                <select id="mySelect" multiple="multiple" class='image-picker' >
                                    %(Images)s
                                    </select>
                            </div>

                            <input value= "Reset" type="button" onclick="resetSel();" >
                            <input value = "Toggle Selection" type='button' onclick="toggleSel();">
                            <input value= "Download Selected" type='button' onclick="getAll();"/>

                        </div>
                    <h3><a href="#">Links</a></h3>
                        <div>
                            <p>%(Links)s
                            </p>
                        </div>
                    <h3><a href="#">Files</a></h3>
                        <div>
                            <p>%(Files)s
                            </p>
                        </div>
                </div>
                </form>
            <script>
            /* Download an img */
            function download(href) {
                var link = document.createElement("a");
                link.href = href;
                link.download = true;
                link.style.display = "none";
                var evt = new MouseEvent("click", {
                    "view": window,
                    "bubbles": true,
                    "cancelable": true
                });

                document.body.appendChild(link);
                link.dispatchEvent(evt);
                document.body.removeChild(link);
                console.log("Downloading href:" + href);
            }

            var element = document.getElementById("mySelect");
            var options = element.options;

            function resetSel(){
                for(var i = 0; i<options.length; i++){
                    options.item(i).selected = false;
                };
                jQuery('select').data('picker').sync_picker_with_select();
            };

            function toggleSel(){
                for(var i = 0; i<options.length; i++){
                    options.item(i).selected = !options.item(i).selected ;
                };
                jQuery('select').data('picker').sync_picker_with_select();
            };

            function getAll(){
                for(var i = 0; i<options.length; i++){
                    if (options.item(i).selected) {
                        download(options.item(i).value);
                    };
                };
            };

            jQuery("select.image-picker").imagepicker({hide_select:  true,});

            </script>
        </body>
        </html>
        """
        elts = dict()
        elts['Images'] = ""
        elts['Links'] = ""
        elts['Files'] = ""
        elts['gameId'] = self.selected_game
        elts['gameName'] = self.ids.details.title.encode('cp1252', 'ignore')
        imgs = []
        for img, href in self.images:
            imgs.append(line%({'img':img, 'href':href.replace('_mt','')}))
        elts['Images'] = "\n".join(imgs)
        sub=tmpl.encode('cp1252', 'ignore')%elts
        file(join(path, "explore_%s.html"%self.selected_game),'wb').write(sub)

        from conf import start_file
        start_file(join(path, "explorer_%s.html"%self.selected_game))

    def create_game_folder(self):
        from conf import gamepath
        "Create Game Folder"
        # ~ 1.Get Current game name
        gameId=self.selected_game
        gameName=self.ids.details.title
        # ~ 2. Create folder for current game name
        import os.path
        path=os.path.join(gamepath,gameName)
        if os.path.isdir(path):
            raise ValueError('Already Existing folder for %s in %s. Aborting'%(gameName,gamepath))
        os.mkdir(path)
        # ~ 3. create subfolders: rule, img, old , export
        os.mkdir(os.path.join(path, 'rules'))
        os.mkdir(os.path.join(path, 'img'))
        os.mkdir(os.path.join(path, 'old'))
        os.mkdir(os.path.join(path, 'export-%s'%gameName))
        output = file(os.path.join(path, 'description.txt'),'wb')
        output.write('Game Description:\n')
        output.write(self.ids.details.ids.description.text)
        output.write('\n\nMore Information:')
        output.write(self.ids.details.ids.information.text)
        from conf import start_file
        start_file(path)

if __name__=='__main__':
    from kivy.logger import Logger
    Logger.setLevel('WARNING')
    from kivy.base import runTouchApp
    runTouchApp((BGGeekBrowser()))
