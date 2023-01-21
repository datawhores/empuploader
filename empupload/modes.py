import yaml
import json
import os
import re
import random
import datetime
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
Get yamlpath based on path

:param path: path chosen by user
:param args: user Commandline/Config arguments

:returns: Proceeds to Upload
"""

def pre_upload_emp(args,path):
    basename=paths.get_upload_name(path)
    yamlpath=None
    if args.input!=None:
        yamlpath=args.input
    elif args.data!=None:
        yamlpath=os.path.join(args.data,f"{basename}.yaml")
    else:
        print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")
        quit()
    upload_emp(yamlpath,args)
"""
Utilizes yaml file to upload

:param yamlpath: path for yaml config
:param args: user Commandline/Config arguments

:returns: None
"""

def upload_emp(yamlpath,args):
    workingdir=runner.get_workdir()
    f=open(yamlpath,"r")
    upload_dict= yaml.safe_load(f)
    dupe,page=puppet.find_dupe(upload_dict,puppet.loadcookie())
    if dupe==True:
        upload=("Ignore dupes and continue upload?: ")
    if dupe!=None  and \
        (dupe==False or upload=="Yes" or upload=="YES" or upload=="Y" or upload=="y" or upload=="YES"):
        puppet.upload_torrent(page,upload_dict)
        



"""
Prepare yaml by Embedding Generated Info

:param path: path chosen by user
:param args: user Commandline/Config arguments
:param yamlpath: path for yaml config

:returns:yamlpath
"""

def process_yaml(path,yamlpath):
    video=None
    audio=None
    console.console.print(f"\nAttempting to Create yaml at {yamlpath}",style="yellow")
    if os.path.isfile(yamlpath) and selection.singleoptions("File Exist Do you want to overwrite",["Yes","No"])=="No":
        return
        createfile=input("File Exist Do you want to overwrite the file? ")
    Path(os.path.dirname(yamlpath)).mkdir( parents=True, exist_ok=True )
    fp=open(yamlpath,"w")
    maxfile=media.find_maxfile(path)
    if maxfile:
        video,audio=media.metadata(maxfile)   
    basename=paths.get_upload_name(path)
    torrentpath=os.path.join(args.prepare.torrent,f"{basename}.torrent")
    picdir=args.prepare.picdir or tempfile.mkdtemp(dir=settings.tmpfile)
    Path(picdir ).mkdir( parents=True, exist_ok=True )
    torrent=Thread(target = create_torrent, args = (path,torrentpath))
    torrent.start()
    emp_dict={}
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    emp_dict["title"]=selection.strinput("Enter Title For Upload: ",default=sug)
    
    emp_dict["category"]=getcat()[selection.singleoptions("Enter Category: ",getcat().keys())]
    # #can we autocomplete tags?
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space: "))
    emp_dict["desc"]=selection.strinput("Enter Description: ",multiline=True)
    gifpath=os.path.join(picdir, f"{os.urandom(24).hex()}.gif")
    emp_dict["cover"]=args.prepare.cover or media.createcovergif(gifpath,maxfile)
    emp_dict["thumbs"]=media.create_images(path,picdir)
    emp_dict["staticimg"]=media.createStaticImagesDict(args.prepare.images)
    emp_dict["media"]={}
    emp_dict["media"]["audio"]=audio
    emp_dict["media"]["video"]=video
    
    console.console.print(f"Torrent Save to {torrentpath}",style="yellow")

    emp_dict["torrent"]=torrentpath
    yaml.dump(emp_dict,fp, default_flow_style=False)
    fp.close()
    console.pprint(emp_dict)

def getcat():
    workingdir=settings.workingdir
    g=open(os.path.join(workingdir,"data/cat.yaml"),"r")
    return yaml.safe_load(g)








"""
Update Upload Template with yaml

:param args: user Commandline/Config arguments
:param yamlpath: path for yaml config

:returns:yamlpath
"""
def update_template(yamlpath):
    # re.search("https://fapping.empornium.sx/images.*",  emp_dict.get("cover",["placeholder"]))
    f=open(yamlpath,"r")
    emp_dict= yaml.safe_load(f)
    f.close()
    emp_dict["title"]=selection.strinput("Enter Title For Upload: ",default=emp_dict["title"])
    emp_dict["taglist"]=re.sub(","," ",selection.strinput("Enter Tags Seperated By Space: ",default=emp_dict['taglist']))
    if selection.singleoptions("Change Category",choices=["Yes","No"])=="Yes":
        emp_dict["category"]=getcat()[selection.singleoptions("Update Category: ",getcat().keys())]
    if selection.singleoptions("Edit Upload String: ",choices=["Yes","No"]):
        emp_dict["template"]=selection.strinput(msg="",default=getPostStr(emp_dict),multiline=True)

    if selection.singleoptions("Do you want to update configuration yaml: ",choices=["Yes","No"])=="Yes":
        fp=open(yamlpath,"w")
        yaml.dump(emp_dict,fp, default_flow_style=False)
        fp.close() 
def getPostStr(emp_dict):
    t=Template(emp_dict.get("template") or templateHelper()) 
    t=t.safe_substitute(
            {"title":emp_dict.get("title","placeholder"),
            "cover":emp_dict.get("cover",["placeholder"]),
                "desc":emp_dict.get("desc",["placeholder"]),
            "thumbs":emp_dict.get("thumbs")
        })
    t=updateTemplateImgHelper(emp_dict["staticimg"],"",t)


def updateTemplateImgHelper(emp_dict,keystr,inputStr):
    for key in emp_dict.keys():
        newkeystr=re.sub("^_","",f"{keystr}_{key}")
        if isinstance(emp_dict.get(key),dict):
            inputStr=updateTemplateImgHelper(emp_dict,key,keystr,inputStr)
        else:
            inputStr=Template(inputStr).safe_substitute({newkeystr:
            
            emp_dict.get(key)})
    return inputStr
            





"""
Creates a Torrent using path and torrentpath

:param path: path chosen by user
:param torrent path: path for torrent file
:param args: user Commandline/Config arguments

:returns: None
"""

def create_torrent(path,torrentpath):
    #make torrent path
    Path( os.path.dirname(torrentpath)).mkdir( parents=True, exist_ok=True )
    t=dottorrent.Torrent(path, trackers=[args.prepare.tracker], private=True,exclude=args.prepare.exclude)
    t.piece_size=min(t.get_info()[2],16777216)
    #Progress Bar
    files = set()
    # pbar = tqdm(
    #     total=t.get_info()[2] * t.get_info()[3] / 1048576,
    #     unit=' MB')
    def progress_callback(fn, pieces_completed, total_pieces):
        if fn not in files:
            # print(fn)
            files.add(fn)
        #verbose
        # print("{}/{} {}".format(pieces_completed, total_pieces, fn))
        # pbar.update(t.get_info()[2] / 1048576)    
    # print("Generating and Saving Torrent File")
    t.generate(progress_callback)
    # pbar.close()
    with open(torrentpath, 'wb') as f:
        t.save(f)
def getrandomPrefix(upload_dict):
    title=upload_dict.get("title","")
    date=datetime.today().strftime('%Y-%m-%d')
    randomstring=''.join(random.choices(string.ascii_lowercase, k=8))
    return f"{date}_{randomstring}_{title}"                 
   
def templateHelper():
    with open(args.edit.template,"r") as p:
      return p.read()

def preview_emp():
    dupe,page=puppet.find_dupe(upload_dict,cookie,randomImageString)
    
       

    if dupe==True:
        upload=input("Ignore dupes and continue upload?: ")
    if dupe!=None  and \
        (dupe==False or upload=="Yes" or upload=="YES" or upload=="Y" or upload=="y" or upload=="YES"):
        puppet.upload_torrent(page,upload_dict,catdict,randomImageString)
        
    
        