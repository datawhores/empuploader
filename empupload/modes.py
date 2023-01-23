import yaml
import os
import re
import shutil
from string import Template
from threading import Thread
import tempfile
import string
from pathlib import Path
import dottorrent
import general.console as console
import empupload.puppet as puppet
import runner as runner
import empupload.media as media
import runner as runner
import general.selection as selection
import settings as settings
import general.arguments as arguments
import general.paths as paths

args=arguments.getargs()

"""
Utilizes yml file to upload

:param ymlpath: path for yml config

:returns: None
"""

def upload(ymlpath):
    fp=open(ymlpath,"r")
    emp_dict= yaml.safe_load(fp)
    emp_dict["template"]=getPostStr(emp_dict)
    puppet.create_chrome()
    dupe,page,dupeurl=puppet.find_dupe(emp_dict,puppet.loadcookie())
    if dupe==True:
        console.console.print(dupeurl,style="yellow")
        if selection.singleoptions("Ignore dupes and continue upload?",["Yes","No"])=="No":
            return
    print(f"{emp_dict['template']}\n")
    console.console.print(puppet.upload_torrent(page,emp_dict),style="yellow")
    fp.close()

        



"""
Prepare yml by embedding generated Info

:param path: path chosen by user
:param ymlpath: path for yaml config

:returns None:
"""

def process_yml(inputFolder,ymlpath):
    video=None
    audio=None
    console.console.print(f"\nAttempting to Create yaml at {ymlpath}",style="yellow")
    paths.setPath()
    if os.path.isfile(ymlpath) and selection.singleoptions("File Exist Do you want to overwrite?",["Yes","No"])=="No":
        return
    Path(os.path.dirname(ymlpath)).mkdir( parents=True, exist_ok=True )
    fp=open(ymlpath,"w")
    maxfile=media.find_maxfile(inputFolder)
    if maxfile:
        video,audio=media.metadata(maxfile)   
    basename=paths.get_upload_name(inputFolder)
    torrentpath=os.path.join(args.prepare.torrent,f"{basename}.torrent")
    picdir=args.prepare.picdir or tempfile.mkdtemp(dir=settings.tmpdir)
    Path(picdir ).mkdir( parents=True, exist_ok=True )
    torrent=Thread(target = create_torrent, args = (inputFolder,torrentpath))
    torrent.start()
    paths.setPath()
    emp_dict={}
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    emp_dict["inputFolder"]=inputFolder
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=sug)
    emp_dict["category"]=paths.getcat()[selection.singleoptions("Enter Category:",paths.getcat().keys())]
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:"))
    emp_dict["desc"]=selection.strinput("Enter Description:",multiline=True)
    emp_dict["cover"]=args.prepare.cover or media.createcovergif(os.path.join(picdir, f"{os.urandom(24).hex()}.gif"),maxfile)
    emp_dict["thumbs"]=media.create_images(inputFolder,picdir)
    emp_dict["staticimg"]=media.createStaticImagesDict(args.prepare.images)
    emp_dict["media"]={}
    emp_dict["media"]["audio"]=audio
    emp_dict["media"]["video"]=video
    
    
    console.console.print(f"Torrent Save to {torrentpath}",style="yellow")

    emp_dict["torrent"]=torrentpath
    yaml.dump(emp_dict,fp, default_flow_style=False)
    fp.close()
    console.pprint(emp_dict)
    shutil.rmtree(picdir,ignore_errors=True)










"""
Update yml config

:param ymlpath: path for yml config

:returns:returns path to updated yml
"""
def update_yml(ymlpath):
    f=open(ymlpath,"r")
    emp_dict= yaml.safe_load(f)

    f.close()
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=emp_dict["title"])
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:",default=emp_dict['taglist']))
    emp_dict["desc"]=selection.strinput("Enter Description: ",multiline=True,default=emp_dict["desc"])
    picdir=tempfile.mkdtemp(dir=settings.tmpdir)
    if selection.singleoptions("Change Category>",choices=["Yes","No"])=="Yes":
        emp_dict["category"]=paths.getcat()[selection.singleoptions("Update Category: ",paths.getcat().keys())]
    if selection.singleoptions("Generate a new cover gif?",choices=["Yes","No"])=="Yes":
        maxfile=media.find_maxfile(emp_dict["inputFolder"])
        emp_dict["cover"]=media.createcovergif(os.path.join(picdir, f"{os.urandom(24).hex()}.gif"),maxfile)
    if selection.singleoptions("Generate New thumbs?",choices=["Yes","No"])=="Yes":
        emp_dict["thumbs"]=media.create_images(emp_dict["inputFolder"],picdir)
    if selection.singleoptions("Edit Upload String?",choices=["Yes","No"])=="Yes":
        emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)
    if selection.singleoptions("Recreate torrent?",choices=["Yes","No"])=="Yes":
        basename=paths.get_upload_name(emp_dict["inputFolder"])
        console.console.print("Making Torren",style="yellow")
        create_torrent(emp_dict["inputFolder"],os.path.join(args.prepare.torrent,f"{basename}.torrent"))
    console.console.print(emp_dict,style="yellow")
    if selection.singleoptions("Do you want to update configuration yml?",choices=["Yes","No"])=="Yes":
        fp=open(ymlpath,"w")
        yaml.dump(emp_dict,fp, default_flow_style=False)
        fp.close() 
    shutil.rmtree(picdir,ignore_errors=True)
"""
Retrive Post string that is used for torrent description

:param emp_dict: Parsed yml file in dict form

:returns str: post string
"""

def getPostStr(emp_dict):
    t=Template(emp_dict.get("template") or templateHelper() or "") 
    t=t.safe_substitute(
            {"title":emp_dict.get("title","placeholder"),
            "cover":emp_dict.get("cover",["placeholder"]),
                "desc":emp_dict.get("desc",["placeholder"]),
            "thumbs":emp_dict.get("thumbs")
        })
    t=updateTemplateImgHelper(emp_dict["staticimg"],t)
    t=updateTemplateMediaInfoHelper(emp_dict["media"]["audio"],emp_dict["media"]["video"],t)
    return t


"""
function to substitute placeholder images in loaded template

:param emp_dict: staticimage key value of config yml

:returns templatestr: str with subsititutions
"""
def updateTemplateImgHelper(emp_dict,inputStr):
    for key in emp_dict.keys():
        inputStr=Template(inputStr).safe_substitute({key:emp_dict[key]["link"]})
    return inputStr
            


"""
:param video: video key value of config yml
:param audio: audio key value of config yml
:inputFolderStr: current template string

:returns templatestr: str with subsititutions
"""
def updateTemplateMediaInfoHelper(audio,video,inputStr):
    for key in audio.keys():
        inputStr=Template(inputStr).safe_substitute({f"audio_{key}":audio[key]})
    for key in video.keys():
        inputStr=Template(inputStr).safe_substitute({f"video_{key}":video[key]})       
    return inputStr




"""
Creates a Torrent using inputFolder and torrentpath

:param path: path chosen by user
:param torrent path: path for torrent file

:returns: None
"""

def create_torrent(inputFolder,torrentpath):
    Path( os.path.dirname(torrentpath)).mkdir( parents=True, exist_ok=True )
    t=dottorrent.Torrent(inputFolder, trackers=[args.prepare.tracker], private=True,exclude=args.prepare.exclude)
    t.piece_size=min(t.get_info()[2],8388608)
    t.generate()
    with open(torrentpath, 'wb') as f:
        t.save(f)               
"""
helper to read args.template file

:returns mtn:path to mtn binary
"""
def templateHelper():
    if args.template:
        with open(args.template,"r") as p:
            return p.read()
    return

"""
generates preview using yml configuration

:params ymlpath: path to configuration 

:returns None:
"""

def generatepreview(ymlpath):
    f=open(ymlpath,"r")
    emp_dict= yaml.safe_load(f)
    emp_dict["template"]=getPostStr(emp_dict)
    puppet.create_chrome()
    previewurl=puppet.create_preview(emp_dict,puppet.loadcookie())
    #print outputs
    console.console.print(f"Template String:\n{emp_dict['template']}\n{previewurl}",style="yellow")

   
   
    
        