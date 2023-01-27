import yaml
import os
import re
import shutil
import tempfile
import string
from threading import Thread
from pathlib import Path
import general.console as console
import empupload.puppet as puppet
import runner as runner
import empupload.media as media
import runner as runner
import general.selection as selection
import settings as settings
import general.arguments as arguments
import general.paths as paths
from Cheetah.Template import Template
import general.torrent as torrent
import asyncio
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
    # print(f"{emp_dict['template']}\n")
    console.console.print(puppet.upload_torrent(page,emp_dict),style="yellow")
    fp.close()

        



"""
Prepare yml by embedding generated Info

:param path: path chosen by user
:param ymlpath: path for yaml config

:returns None:
"""

async def process2_yml(inputFolder,ymlpath):
    video=None
    audio=None
    console.console.print(f"\nAttempting to Create yaml at {ymlpath}",style="yellow")
    paths.setPath()
    if os.path.isfile(ymlpath) and selection.singleoptions("File Exist Do you want to overwrite?",["Yes","No"])=="No":
        return
    Path(os.path.dirname(ymlpath)).mkdir( parents=True, exist_ok=True )
    fp=open(ymlpath,"w")
    files=None
    if os.path.isdir(inputFolder):
        files=paths.search(inputFolder,".*",recursive=True,exclude=args.prepare.exclude)
        if args.prepare.manual:
            files=selection.multioptions("Select Files from folder to upload",files)
    else:
        files=[inputFolder]
    maxfile=media.find_maxfile(files)
    if maxfile:
        video,audio=media.metadata(maxfile)   
    basename=paths.get_upload_name(inputFolder)
    torrentpath=os.path.join(args.prepare.torrent,f"{basename}.torrent")
    picdir=args.prepare.picdir or tempfile.mkdtemp(dir=settings.tmpdir)
    Path(picdir ).mkdir( parents=True, exist_ok=True )
    emp_dict={}
    asyncio.create_task(backgroundtask(inputFolder,files,torrentpath,picdir,maxfile,emp_dict),)





   

  
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    emp_dict["inputFolder"]=inputFolder
    emp_dict["inputFiles"]=set(files)
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=sug)
    emp_dict["category"]=paths.getcat()[selection.singleoptions("Enter Category:",paths.getcat().keys())]
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:"))
    emp_dict["desc"]=selection.strinput("Enter Description:",multiline=True)
    emp_dict["staticimg"]=media.createStaticImagesDict(args.prepare.images)
    emp_dict["mediaInfo"]={}
    emp_dict["mediaInfo"]["audio"]=audio
    emp_dict["mediaInfo"]["video"]=video


    if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":
        emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True) 
    emp_dict["torrent"]=torrentpath

    console.console.print(f"Torrent Save to {torrentpath}",style="yellow")
    yaml.dump(emp_dict,fp, default_flow_style=False)
    fp.close()
    console.console.print(emp_dict)










"""
Update yml config

:param ymlpath: path for yml config

:returns:returns path to updated yml
"""
def update_yml(ymlpath):
    f=open(ymlpath,"r")
    emp_dict= yaml.safe_load(f)
    f.close()
    paths.setPath()
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=emp_dict["title"])
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:",default=emp_dict['taglist']))
    emp_dict["desc"]=selection.strinput("Enter Description for upload: ",multiline=True,default=emp_dict["desc"])
    picdir=tempfile.mkdtemp(dir=settings.tmpdir)
    if selection.singleoptions("Change Category",choices=["Yes","No"])=="Yes":
        emp_dict["category"]=paths.getcat()[selection.singleoptions("Update Category: ",paths.getcat().keys())]
    if selection.singleoptions("Generate a new cover gif?",choices=["Yes","No"])=="Yes":
        maxfile=media.find_maxfile(emp_dict["inputFolder"])
        emp_dict["cover"]=media.createcovergif(os.path.join(picdir, f"{os.urandom(24).hex()}.gif"),maxfile)
    if selection.singleoptions("Generate new screens?",choices=["Yes","No"])=="Yes":
        emp_dict["screens"]=media.create_images(emp_dict["inputFolder"],picdir)
    if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":
        emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)
    if selection.singleoptions("Recreate torrent file?",choices=["Yes","No"])=="Yes":
        basename=paths.get_upload_name(emp_dict["inputFolder"])
        console.console.print("Making Torren",style="yellow")
        torrent.create_torrent(emp_dict["inputFolder"],emp_dict["inputFiles"],os.path.join(args.prepare.torrent,f"{basename}.torrent"))
    console.console.print(emp_dict,style="yellow")
    if selection.singleoptions("Do you want to save your changes?",choices=["Yes","No"])=="Yes":
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
    nameSpace={
            "title":emp_dict.get("title","placeholder"),
            "cover":emp_dict.get("cover",["placeholder"]),
                "desc":emp_dict.get("desc",["placeholder"]),
            "screens":emp_dict.get("screens")
        }
    nameSpace.update(emp_dict["staticimg"])
    nameSpace.update(templateMediaInfoHelper(emp_dict["mediaInfo"]["audio"],emp_dict["mediaInfo"]["video"]))
    nameSpace.update({"torrent":emp_dict["torrent"],"args":args,"inputFolder":emp_dict["inputFolder"]})
    t = Template((emp_dict.get("template") or templateHelper() or ""),searchList=[nameSpace])
    return str(t)

        
            


"""
:param video: video key value of config yml
:param audio: audio key value of config yml
:inputFolderStr: current template string

:returns templatestr: str with subsititutions
"""
def templateMediaInfoHelper(audio,video):
    namespace={}
    for key in audio.keys():
        namespace.update({f"audio_{key}":audio[key]})
    for key in video.keys():
        namespace.update({f"video_{key}":video[key]})    
    return namespace





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

   
   
    
async def backgroundtask(inputFolder,files,torrentpath,picdir,maxfile,emp_dict):
    emp_dict["screens"]=media.create_images(files,inputFolder,picdir) 
    emp_dict["cover"]=args.prepare.cover or media.createcovergif(os.path.join(picdir, f"{os.urandom(24).hex()}.gif"),maxfile)
    media.cleanup(picdir)
    torrent.create_torrent(inputFolder,set(files),torrentpath)
    shutil.rmtree(picdir,ignore_errors=True)


def process_yml(inputFolder,ymlpath):
    video=None
    audio=None
    console.console.print(f"\nAttempting to Create yaml at {ymlpath}",style="yellow")
    paths.setPath()
    if os.path.isfile(ymlpath) and selection.singleoptions("File Exist Do you want to overwrite?",["Yes","No"])=="No":
        return
    Path(os.path.dirname(ymlpath)).mkdir( parents=True, exist_ok=True )
    files=None
    if os.path.isdir(inputFolder):
        files=paths.search(inputFolder,".*",recursive=True,exclude=args.prepare.exclude)
        if args.prepare.manual:
            files=selection.multioptions("Select Files from folder to upload",files)
    else:
        files=[inputFolder]
    maxfile=media.find_maxfile(files)
    basename=paths.get_upload_name(inputFolder)
    torrentpath=os.path.join(args.prepare.torrent,f"{basename}.torrent")
    picdir=args.prepare.picdir or tempfile.mkdtemp(dir=settings.tmpdir)
    Path(picdir ).mkdir( parents=True, exist_ok=True )
    emp_dict={}
    backgroundthread=Thread(target=asyncio.run,args=(process_yml_helper(inputFolder,files,torrentpath,picdir,maxfile,emp_dict),))
    backgroundthread.start()
    fp=open(ymlpath,"w")
    video=None
    audio=None
    if maxfile:
        video,audio=media.metadata(maxfile)   
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    emp_dict["inputFolder"]=inputFolder
    emp_dict["inputFiles"]=set(files)
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=sug)
    emp_dict["category"]=paths.getcat()[selection.singleoptions("Enter Category:",paths.getcat().keys())]
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:"))
    emp_dict["desc"]=selection.strinput("Enter Description:",multiline=True)
    emp_dict["staticimg"]=media.createStaticImagesDict(args.prepare.images)
    emp_dict["mediaInfo"]={}
    emp_dict["mediaInfo"]["audio"]=audio
    emp_dict["mediaInfo"]["video"]=video
    backgroundthread.join()

async def process_yml_helper(inputFolder,files,torrentpath,picdir,maxfile,emp_dict):
    task = asyncio.create_task(backgroundtask(inputFolder,files,torrentpath,picdir,maxfile,emp_dict))
    await task
   


    # if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":
    #     emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True) 
    # emp_dict["torrent"]=torrentpath
    # await task
    # console.console.print(f"Torrent Save to {torrentpath}",style="yellow")
    # yaml.dump(emp_dict,fp, default_flow_style=False)
    # fp.close()
    # console.console.print(emp_dict)



