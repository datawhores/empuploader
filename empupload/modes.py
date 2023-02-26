import yaml
import os
import re
import shutil
import tempfile
import traceback
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

def process_yml(inputPath,ymlpath):
    p=paths.NamedTemporaryFile(suffix=".yml")
    fp=open(p,"w")
    tempPicDir=args.prepare.picdir or tempfile.mkdtemp(dir=settings.tmpdir)
    try:
        video=None
        audio=None
        console.console.print(f"\nAttempting to Create yaml at {ymlpath}",style="yellow")
        if os.path.isfile(ymlpath) and selection.singleoptions("File Exist Do you want to overwrite?",["Yes","No"])=="No":
            return
        files=None
        if os.path.isdir(inputPath):
            files=paths.search(inputPath,".*",recursive=True,exclude=[os.path.join(inputPath,"thumbnail.zip"),os.path.join(inputPath,"screens")]+args.prepare.exclude)
            if args.prepare.manual:
                files=selection.multioptions("Select Files from folder to upload",files,transformer=lambda result: f"Number of files selected: {len(result)}")
        else:
            files=[inputPath]
        maxfile=media.find_maxfile(files)
        if maxfile:
            video,audio=media.metadata(maxfile)   
        basename=paths.get_upload_name(inputPath)
        Path(tempPicDir ).mkdir( parents=True, exist_ok=True )
        emp_dict={} 
        sug=re.sub("\."," ",basename)
        sug=string.capwords(sug)
        emp_dict["inputPath"]=inputPath
        emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=sug)
        emp_dict["category"]=paths.getcat()[selection.singleoptions("Enter Category:",paths.getcat().keys())]
        emp_dict["taglist"]=_tagfixer(selection.strinput("Enter Tags Seperated By Space:"))
        emp_dict["desc"]=selection.strinput("Enter Description:",multiline=True)
        emp_dict["staticimg"]=media.createStaticImagesDict(args.prepare.images) or {}
        emp_dict["mediaInfo"]={}
        emp_dict["mediaInfo"]["audio"]=audio or {}
        emp_dict["mediaInfo"]["video"]=video or {}
        emp_dict["tracker"]=args.prepare.tracker
        emp_dict["exclude"]=args.prepare.exclude
        emp_dict["cover"]=media.createcovergif(tempPicDir,maxfile)
        media.create_images(files,tempPicDir)
        imgfiles,imglocation=media.zip_images(inputPath,tempPicDir)
        files.extend(imgfiles)
        emp_dict["screensDir"]=imglocation

        emp_dict["screens"]=media.upload_images(media.imagesorter(tempPicDir))
        emp_dict["torrent"]=torrent.create_torrent(os.path.join(args.prepare.torrent,f"{basename}.torrent"),inputPath,files,tracker=args.prepare.tracker)
        if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":
            emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)

        console.console.print(f"Torrent Save to {emp_dict['torrent']}",style="yellow")
        yaml.dump(emp_dict,fp, default_flow_style=False)
        Path(os.path.dirname(ymlpath)).mkdir( parents=True, exist_ok=True )
        shutil.copyfile( p,ymlpath)
        console.console.print(emp_dict)
    except Exception as E:
        console.console.print(E)
        console.console.print(traceback.format_exc())
    finally:
        paths.rm( tempPicDir)
        fp.close()
        paths.remove(p)









"""
Update yml config

:param ymlpath: path for yml config

:returns:returns path to updated yml
"""
def update_yml(ymlpath):
    mirrorDir=None
    try:
        f=open(ymlpath,"r")
        emp_dict= yaml.safe_load(f)
        f.close()
        baseName=Path(emp_dict["inputPath"]).name
        mirrorDir=str(Path(tempfile.mkdtemp(dir=settings.tmpdir),baseName))
        Path(mirrorDir).mkdir()
        os.chdir(mirrorDir)

        if Path(emp_dict["inputPath"]).is_file():
            Path(emp_dict["inputPath"]).symlink_to(Path(baseName),target_is_directory=True)
        else:
            for p in Path(emp_dict["inputPath"]).iterdir()  :
                if p.name=="screens.zip" or p.name=="screens":
                    continue
                Path(p.name).symlink_to(p,target_is_directory=p.is_dir())
            
                
        emp_dict["title"]=selection.strinput("Enter Title For Upload:",default=emp_dict["title"])
        emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space:",default=emp_dict['taglist']))
        emp_dict["desc"]=selection.strinput("Enter Description for upload: ",multiline=True,default=emp_dict["desc"])
        if selection.singleoptions("Change Category",choices=["Yes","No"])=="Yes":
            emp_dict["category"]=paths.getcat()[selection.singleoptions("Update Category: ",paths.getcat().keys())]  
        temptorrent=paths.NamedTemporaryFile(suffix=".torrent")
        tempPicDir=tempfile.mkdtemp(dir=settings.tmpdir)
        newScreensDir=None
        if selection.singleoptions("Update file selection\nNote This will recreate screens",choices=["Yes","No"])=="Yes":    
            allFiles=paths.search(".",".*",recursive=True,exclude=emp_dict["exclude"])
            files=selection.multioptions("Select files from folder to upload",allFiles,transformer=lambda result: f"Number of files selected: {len(result)}")
            if selection.singleoptions("Generate a new cover gif?",choices=["Yes","No"])=="Yes":
                maxfile=media.find_maxfile(files)
                emp_dict["cover"]=media.createcovergif(tempPicDir,maxfile)
            media.create_images(files,tempPicDir)
            imgfiles,newScreensDir=media.zip_images(mirrorDir,tempPicDir)
            emp_dict["screens"]=media.upload_images(media.imagesorter(tempPicDir))
            files.extend(imgfiles)
            torrent.create_torrent(temptorrent,mirrorDir,files,tracker=emp_dict["tracker"])
        if selection.singleoptions("Manually Edit the upload page 'Description' Box",choices=["Yes","No"])=="Yes":

            emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)
        else:
            emp_dict["template"]=getPostStr(emp_dict)

        console.console.print(emp_dict,style="yellow")
        if selection.singleoptions("Do you want to save your changes?",choices=["Yes","No"])=="Yes":
            
            paths.move(temptorrent,emp_dict["torrent"])
            paths.rm(emp_dict["screensDir"]) 
            paths.move(newScreensDir,emp_dict["inputPath"])
            emp_dict["screensDir"]=str(Path(emp_dict["inputPath"]).joinpath(Path(newScreensDir).name))
            fp=open(ymlpath,"w")
            yaml.dump(emp_dict,fp, default_flow_style=False)
            fp.close() 
         
    except Exception as E:
        console.console.print(E)
        console.console.print(traceback.format_exc())
    finally:
        #force removal
        paths.rm( tempPicDir)
        paths.rm(temptorrent)
        paths.rm(mirrorDir)
       
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
    nameSpace.update({"torrent":emp_dict["torrent"],"args":args,"inputPath":emp_dict["inputPath"]})
    t = Template((emp_dict.get("template") or templateHelper() or ""),searchList=[nameSpace])
    return str(t)

        
            


"""
:param video: video key value of config yml
:param audio: audio key value of config yml
:inputPathStr: current template string

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