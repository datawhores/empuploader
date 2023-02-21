import yaml
import os
import re
import shutil
import tempfile
import string
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
    console.console.print(puppet.upload_torrent(emp_dict),style="yellow")
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
    if os.path.isfile(ymlpath) and selection.singleoptions("File Exist Do you want to overwrite?",["Yes","No"])=="No":
        return
    temp=tempfile.NamedTemporaryFile(suffix=".yml").name
    fp=open(temp,"w")
    files=None
    if os.path.isdir(inputFolder):
        files=paths.search(inputFolder,".*",recursive=True,exclude=[os.path.join(inputFolder,"thumbnail.zip"),os.path.join(inputFolder,"screens")]+args.prepare.exclude)
        if args.prepare.manual:
            files=selection.multioptions("Select Files from folder to upload",files,transformer=lambda result: f"Number of files selected: {len(result)}")
    else:
        files=[inputFolder]
    maxfile=media.find_maxfile(files)
    if maxfile:
        video,audio=media.metadata(maxfile)   
    basename=paths.get_upload_name(inputFolder)
    picdir=args.prepare.picdir or tempfile.mkdtemp(dir=settings.tmpdir)
    Path(picdir ).mkdir( parents=True, exist_ok=True )
    emp_dict={} 
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    emp_dict["inputFolder"]=inputFolder
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=sug)
    emp_dict["category"]=paths.getcat()[selection.singleoptions("Enter Category:",paths.getcat().keys())]
    emp_dict["taglist"]=_tagfixer(selection.strinput("Enter Tags Seperated By Space:"))
    emp_dict["desc"]=selection.strinput("Enter Description:",multiline=True)
    emp_dict["staticimg"]=media.createStaticImagesDict(args.prepare.images)
    emp_dict["mediaInfo"]={}
    emp_dict["mediaInfo"]["audio"]=audio
    emp_dict["mediaInfo"]["video"]=video 
    emp_dict["tracker"]=args.prepare.tracker
    emp_dict["exclude"]=args.prepare.exclude



    emp_dict["cover"]=media.createcovergif(os.path.join(picdir, f"{os.urandom(24).hex()}.gif"),maxfile)
    files.extend(media.create_images(files,inputFolder,picdir))

    emp_dict["screens"]=media.upload_images(media.imagesorter(picdir))
    emp_dict["torrent"]=torrent.create_torrent(os.path.join(args.prepare.torrent,f"{basename}.torrent"),inputFolder,files,tracker=args.prepare.tracker)
    if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":
        emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)

    console.console.print(f"Torrent Save to {emp_dict['torrent']}",style="yellow")
    yaml.dump(emp_dict,fp, default_flow_style=False)
    fp.close()
    Path(os.path.dirname(ymlpath)).mkdir( parents=True, exist_ok=True )
    shutil.move( temp,ymlpath)
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
    emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=emp_dict["title"])
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:",default=emp_dict['taglist']))
    emp_dict["desc"]=selection.strinput("Enter Description for upload: ",multiline=True,default=emp_dict["desc"])
    if selection.singleoptions("Change Category",choices=["Yes","No"])=="Yes":
        emp_dict["category"]=paths.getcat()[selection.singleoptions("Update Category: ",paths.getcat().keys())]
    
    if selection.singleoptions("Update file selection",choices=["Yes","No"])=="Yes":
        allFiles=paths.search(emp_dict["inputFolder"],".*",recursive=True,exclude=[os.path.join(emp_dict["inputFolder"],"thumbnail.zip"),os.path.join(emp_dict["inputFolder"],"screens")]+emp_dict["exclude"])
        files=selection.multioptions("Select files from folder to upload",allFiles,transformer=lambda result: f"Number of files selected: {len(result)}")
        picdir=tempfile.mkdtemp(dir=settings.tmpdir)
    
        
        if selection.singleoptions("Generate a new cover gif?",choices=["Yes","No"])=="Yes":
            maxfile=media.find_maxfile(files)
            emp_dict["cover"]=media.createcovergif(os.path.join(picdir, f"{os.urandom(24).hex()}.gif"),maxfile)
        files.extend(media.create_images(files,emp_dict["inputFolder"],picdir))
        media.upload_images(media.imagesorter(picdir))
        shutil.rmtree(picdir,ignore_errors=True)
        temptorrent=tempfile.NamedTemporaryFile(suffix=".torrent").name
        torrent.create_torrent(temptorrent,emp_dict["inputFolder"],files,tracker=emp_dict["tracker"])
    if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":
        Path(emp_dict["torrent"]).unlink(missing_ok=True)
        shutil.copy(temptorrent,emp_dict["torrent"])
        emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)
    else:
        emp_dict["template"]=getPostStr(emp_dict)

    console.console.print(emp_dict,style="yellow")
    if selection.singleoptions("Do you want to save your changes?",choices=["Yes","No"])=="Yes":
        fp=open(ymlpath,"w")
        yaml.dump(emp_dict,fp, default_flow_style=False)
        fp.close() 
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
    previewurl=puppet.create_preview(emp_dict)
    #print outputs
    console.console.print(f"Template String:\n{emp_dict['template']}\n-------------------------------\n{previewurl}",style="yellow")
"""
Fixes formating of taglist

:params taglist: taglist

:returns taglist: fixed taglist string
"""
   
def _tagfixer(taglist):
    taglist= re.sub(" *\.",".",taglist)
    taglist=re.sub(" +"," ",taglist)
    taglist= re.sub(" ",",",taglist)
    return re.sub(",+",",",taglist)