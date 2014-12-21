"""All things specific the MSE communication"""
import os, os.path, codecs
import wx
from collections import OrderedDict 
from config import MSE_VERSION, card_folder
from wx.lib.wordwrap import wordwrap

from widgets import *

##
ENUMS={
    'card list alignment':['left','center','right','top','middle','bottom','justify','justify-all','strech','if-overflow','force'],
    'alignment':['left','center','right','top','middle','bottom','justify','justify-all','strech','if-overflow','force'],
    'popup style':['drop down', 'in place'],
    'render style':['text', 'image','both','hidden','image hidden','checklist','image checklist','both checklist','text list','image list','both list'],
    'direction':['horizontal','vertical'],
    'combine':[
                'normal','add','subtract','stamp','difference',
                'negation','multiply','darken','lighten','color dodge','color burn',
                'screen','overlay','hard light','soft light','reflect','glow',
                'freeze','heat','and','or','xor','shadow','symmetric overlay'
    ]
}

def CopyImage(obj,game_folder,style_folder):
    """Find any propery for the given page. If of type img, file or choice image, change the value to simple path & copy image to destination"""
    import os.path
    from shutil import copy
    #if no image=>return
    if obj.Type in ('Set','Info'):
        return
    vs=obj.GetValues()
    folders=[game_folder,style_folder]
    xfos=[correspondance,corresp_style]
    for folder,xfo in zip(folders,xfos):
        target=xfo[obj.Type]()
        target.fromObj(obj)
        for _name in target.params:
            _t,_v=target.params[_name]
            if _t in ('file','img'):
                #Ensure the file exist or is defined before copying it
                if not _v:
                    continue
                if not os.path.isfile(_v):
                    continue
                #Copying file if they exists
                copy(_v,folder)
                #Converting the source before exporting the text=> done in the export method of the class
            if _t=="imglist":
                if hasattr(target,"_choices"):
                    #_v is an ordereddict which link choice key to path. Copy all the paths
                    for path in target._choices.values():
                        if os.path.isfile(path):
                            copy(path,folder)
    
def GenerateSetFiles(elements,dst_dir,startfile=True):
    import os.path,os,zipfile
    import csv,shutil
    TARGET='mse_gen'
    sets=list()
    cardElements=[elt for elt in elements if elt.Type not in ('Template','Set','Info','Color')]
    card_template=os.linesep.join(["card:"]+["\t%s: %%(%s)s"%(elt.GetValues()['name'],elt.GetValues()['name']) for elt in cardElements])
    fileElts=[elt for elt in elements if elt.Type in ('Image','StaticImage')]
    txtElts=[elt for elt in elements if elt.Type in ('Text')]
    #First get actuel game Name
    game_name=elements[0].GetValues()['short name']
    style_name=elements[0].GetValues()['style short name']
    #The loop on each set to create
    for eltIndex,elt in enumerate(elements):
        if elt.Type!='Set':
            continue
        vs=elt.GetValues()
        name=vs['name']
        if not name:
            name='untitledSet%d'%eltIndex
        strings=[]
        #Header
        elt.game_name=game_name
        elt.style_name=style_name
        strings.append(FieldFromValues(elt.Type,elt).export())
        xl=vs['excel cards file']
        if not xl:
            print  '[warning,not excel file provided]'
        if not os.path.isfile(xl):
            print '[warning: set excel file for set %s is not existing - skipping'%vs['name']
            continue
        cards=csv.reader(file(xl,'rb'), delimiter=';')
        #Get The labels:
        #First check if the first line is fitting size. If that, take the second one for label, otherwise the first
        labels=None
        isOldStyle=False
        for i,c in enumerate(cards):
            if i==0:
                if c[0]=='Fitting Size':
                    isOldStyle=True
                    continue
            labels=c
            break
        #Now, create the list of labels present in the template but not in CSv. Warn about them
        skipElts=[elt.GetValues()['name'] for elt in cardElements if elt.GetValues()['name'] not in labels]
        for _skip in skipElts:
            print '[WARNING] Template column %s does not exist in CSV file. Adding a blank one'%_skip
        cards=csv.DictReader(file(xl,'rb'),fieldnames=labels,delimiter=";")
        #Loop on cards:
        for lineindex,line in enumerate(cards):
            if lineindex==0:#skip first line
                continue
            if lineindex==1 and  isOldStyle:
                continue
            for i in range(int(line['Qt'])):
                for elt in fileElts:
                    if i: #if more than one card, we already did it ! 
                        break
                    _name=elt.GetValues()['name']
                    #check if name exist in template. otherwise, skip & continie, issue a warning
                    if _name in skipElts:
                        line[_name]=""
                        continue
                    #copy file then change line value
                    if os.path.isfile(line[_name]):
                        shutil.copy(line[_name],TARGET)
                    line[_name]=os.path.split(line[_name])[1]
                for elt in txtElts:
                    _name=elt.GetValues()['name']
                    _lines=line[_name].splitlines()
                    if len(_lines)>1:
                        line[_name]="\n\t\t"+line[_name].replace('\n','\n\t\t')
                strings.append(card_template.encode('cp1252')%line)
        _ss=[s.decode('cp1252') for s in strings]
        _sss=os.linesep.join(_ss).encode('utf-8')
        file(os.path.join(TARGET,'set'),'wb').write(_sss)
        #Now copying images !!
        for eltim in elements:
            CopyImage(eltim,TARGET,TARGET)
        #Now zip the file
        from glob import glob
        from zipfile import ZipFile,ZIP_DEFLATED
        arch=ZipFile(os.path.join(dst_dir,name+".mse-set"),'w',compression=ZIP_DEFLATED)
        for fs in glob(os.path.join(TARGET,'*')):
            arch.write(fs,arcname=os.path.split(fs)[1])
            os.remove(fs)
        arch.close()
        sets.append(os.path.join(dst_dir,name+".mse-set"))
    if startfile: os.startfile(dst_dir)
    return sets

def GenerateImages(setname,dst_dir,extension='jpg'):
    from config import MSE_PATH
    import os.path
    if not os.path.isfile(MSE_PATH):
        print "request_new_mse_path"
    dst=os.path.join(dst_dir,'image.%s'%extension)
    os.system(r'""%s" --export "%s" "%s""'%(MSE_PATH,setname,dst))
    
def ImportTemplate(fname,dst):
    game,style=fname.split('-',1)
    import os.path
    from os.path import join
    from config import MSE_PATH
    thedir,mse=os.path.split(MSE_PATH)
    src=os.path.join(thedir,'data')
    if not os.path.isdir(src):
        raise ValueError('MSE Path does not exists')
    gamePath=os.path.join(src,game+".mse-game")
    stylePath=os.path.join(src,fname+".mse-style")
    from collections import OrderedDict
    elts=OrderedDict()
    Template=GameTemplate()
    elts['Template']=Template
    Template.USED=True
    for fpath,fname in zip((gamePath,stylePath),('game','style')):
        #First read game template
        stack=[]
        for line in file(join(fpath,fname),'rb'):
            line=line.lstrip(  codecs.BOM_UTF8 )
            stack=handle(line,stack,elts,fpath)
    usedelts=OrderedDict()
    for name,value in elts.items():
        print name,value.USED        
        if value.USED:
            delattr(value,'USED')
            usedelts[name]=value
    return usedelts

def handle(line,stack,elts,fpath):
    if line.strip().startswith('#'):
        return stack
    if not line.strip():
        return stack
    if line.startswith('\t'):
        stack.append(line)
        return stack
    if not line.strip().split(':',1)[1]:#no right member behind ':'=> it a NEW object
        #First process the existing stac
        GenElt(stack,elts,fpath)
        stack=[]
        stack.append(line)
        return stack
    if stack:  
        GenElt(stack,elts,fpath)
        stack=[]
    GenElt([line],elts,fpath)
    return stack

def GenElt(stack,elts,fpath):
    if not stack:
        return
    if stack[0].split(':',1)[0].strip()=='include file':
        fname=stack[0].split(':',1)[1].strip()
        substack=[]        
        for line in file(os.path.join(fpath,fname),'rb'):
            line=line.lstrip(  codecs.BOM_UTF8 )
            substack=handle(line,substack, elts,fpath)
        return
    if len(stack)==1:
        elts['Template'].fromText(stack[0])
        return
    if stack[0].split(':',1)[0].strip()=='depends on':
        print 'Depends on multiline to be processed:',stack
        return    
    if stack[0].strip()=='card field:':
        #Create the elt
        del stack[0]
        #First get the type of the elt
        for line in stack:
            l,r=line.strip().split(':',1)
            if l=='type':
                break
        elt=ElementsClass[r.strip()]()
        for line in stack:
            if line.startswith('\t\t'):
                #Very specific case. to be studied later on
                continue
            elt.fromText(line)
        if "name" in elt.params:
            elt.name=elt['name']
            print 'Creating elt %s(%s)'%(elt.name,elt)
        elts[elt.name]=elt
        elt.USED=False
        return
    if stack[0].startswith('\t\tfont:'):
        #print 'skipping font'
        #return
        font=FontTemplate()
        for line in stack[1:]:
            font.fromText(line)
        #print elts.keys()[-1],elts.values()[-1]
        elts.values()[-1].params['font']=font
        return
    if stack[0].startswith('\t\tscript:'):
        print 'trying to handle script -%d sized stack'%len(stack)      
        return  
    elif stack[0].split(':',1)[0].strip() in elts:#Start of a style for a given element
        name=stack[0].split(':',1)[0].strip()
        del stack[0]
        elt=elts[name]
        elt.USED=True
        for line in stack:
            try:
                elt.fromText(line)
            except:
                print '###: issue when %s imports line "%s"'%(elt,line)
        return
    elif stack[0].split(':',1)[0].strip()=="init script":
        script=''.join(stack).split(':',1)[1]
        elts['Template']['init script']=script
    elif stack[0].split(':',1)[0].strip()=="card style":
        del stack[0]
        substack=[]
        for l in stack:
            #remove the initial \t char
            substack=handle(l[1:],substack,elts,fpath)
    elif stack[0].split(':',1)[0].strip()=="keyword":
        elt=ElementsClass['keyword']()
        for line in stack:
            try:
                elt.fromText(line)
            except:
                print '[Issue with]',line
        if "keyword" in elt.params:
            elt.name=elt['keyword']
        elts[elt.name]=elt
        elt.USED=False
    elif stack[0].split(':',1)[0].strip()=="word list":
        elt=ElementsClass['wordlist']()
        for line in stack:
            try:
                elt.fromText(line)
            except:
                print '[Issue with]',line
        if "name" in elt.params:
            elt.name=elt['name']
        elts[elt.name]=elt
        elt.USED=False
    else:
        print '[Unkown stack of length %d]: Startswith'%len(stack),stack[0]
