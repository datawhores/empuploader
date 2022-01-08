import subprocess
import empupload.general as general
import yaml
import json
import os
import empupload.puppet as puppet
import empupload.general as general
import empupload.media as media
from threading import Thread
import tempfile
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt as input
import string
import re
from pprint import pprint

"""
Creates a Torrent using path and torrentpath

:param path: path chosen by user
:param torrent path: path for torrent file
:param args: user Commandline/Config arguments

:returns: None
"""

def create_torrent(path,torrentpath,args):
   print("Creating torrent")
   torrent=subprocess.run([args.dottorrent,'-p','-t',args.trackerurl,'-s','8M','--exclude',"*.yaml",path,torrentpath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


"""
Get yamlpath based on path

:param path: path chosen by user
:param args: user Commandline/Config arguments

:returns: Proceeds to Upload
"""

def pre_upload_emp(args,path):
    basename=general.get_upload_name(path)
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
    workingdir=general.get_workdir()
    f=open(yamlpath,"r")
    upload_dict= yaml.safe_load(f)
    g=open(os.path.join(workingdir,"cat.yaml"),"r")
    catdict= yaml.safe_load(g)
    cookie=None
    if args.cookie==None or args.cookie=="":
        print("You need a cookie file")
        quit()
    else:
        g=open(args.cookie,"r")
        cookie=json.load(g)

    dupe,page=puppet.find_dupe(upload_dict,cookie)
    
       

    if dupe==True:
        upload=input("Ignore dupes and continue upload?: ")
    if dupe!=None  and \
        (dupe==False or upload=="Yes" or upload=="YES" or upload=="Y" or upload=="y" or upload=="YES"):
        puppet.upload_torrent(page,upload_dict,catdict)
        

"""
Get yamlpath based on path

:param basename: Path with only last section remaining
:param args: user Commandline/Config arguments

:returns:yamlpath
"""
def start_yaml(basename,args):
    yamlpath=None
    print("Finding Largest File for Metadata/Covers")
    if args.input!=None:
        yamlpath=args.input
    elif args.data!=None:
        yamlpath=os.path.join(args.data,f"{basename}.yaml")
    else:
        print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")
    return yamlpath
"""
Prepare yaml by Embedding Generated Info

:param path: path chosen by user
:param args: user Commandline/Config arguments
:param yamlpath: path for yaml config

:returns:yamlpath
"""

def process_yaml(path,args,yamlpath):
    createfile="Yes"
    print("\nAttempting to Create yaml at",yamlpath)
    if os.path.isfile(yamlpath):
        createfile=input("File Exist Do you want to overwrite the file? ")
    if createfile!="Yes" and createfile!="yes" and createfile!="y" and createfile!="Y" and createfile!="YES":
        return
    fp=open(yamlpath,"w")

    maxfile=media.find_maxfile(path,args)

    basename=general.get_upload_name(path)
    video,audio=media.metadata(maxfile)   
    workingdir=general.get_workdir()
    g=open(os.path.join(workingdir,"cat.yaml"),"r")
    catdict= yaml.safe_load(g)
    torrentpath=os.path.join(args.torrents,f"{basename}.torrent")
    picdir=os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}/")
    if args.screens!=None:
        picdir=args.screens


    try:
        os.mkdir(picdir)
    except Exception as e:
        print(e)
    torrent=Thread(target = create_torrent, args = (path,torrentpath,args))
    torrent.start()
    emp_dict={}
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    print("\nPress Tab for Auto Suggestion")
    emp_dict["title"]=input("Enter Title: ",completer=WordCompleter([sug],ignore_case=True))
    print("\nPress Tab for Auto Suggestion")

    emp_dict["category"]=input("Enter Category: ",completer=WordCompleter(catdict.keys(),ignore_case=True))
    #can we autocomplete tags?
    print("\nEnter Space seperated tags")

    emp_dict["taglist"]=re.sub(","," ",input("Enter Tags: "))
    print("\nPress [Meta+Enter] or [Esc] followed by [Enter] to accept input.")
    emp_dict["desc"]=input("Enter Description: ",multiline=True)
    
    gifpath=os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}.gif")
    emp_dict["cover"]=media.createcovergif(gifpath,maxfile,args)

    emp_dict["thumbs"]=media.create_images(path,picdir,args)
    emp_dict["audio"]=audio
    emp_dict["video"]=video
    emp_dict["images"]=general.set_template_img(args)
    matches=[]
    h=""
    if args.template!=None and os.path.isfile(args.template):
        h=open(args.template,"r")
        h=h.readlines()
        h=''.join(h)
        matches=re.findall("{.*}",h)
    for element in matches:
        key=re.sub("{|}","",element).lower()
        if re.search("video",element):
            key=key.split(".")[1]
            value=emp_dict["video"].get(key,"")
        elif re.search("audio",element):
            key=key.split(".")[1]
            value=emp_dict["audio"].get(key,"")
        elif re.search("images",element):
            key=key.split(".")[1]
            value=emp_dict["images"].get(key,"")
        else:
             value=emp_dict.get(key,"")
        h=re.sub(element,value,h)

    emp_dict["template"]=h
    torrent.join()
    emp_dict["torrent"]=torrentpath
    yaml.dump(emp_dict,fp, default_flow_style=False)
    fp.close()
    pprint(emp_dict,width=1)



"""
Update Upload Template with yaml

:param args: user Commandline/Config arguments
:param yamlpath: path for yaml config

:returns:yamlpath
"""
def update_template(args,yamlpath):
    f=open(yamlpath,"r")
    emp_dict= yaml.safe_load(f)
    f.close()
    if args.template==None:
        print("Please Provide a Template via the commandline or configfile")
    h=open(args.template,"r")
    h=h.readlines()
    h=''.join(h)
    matches=re.findall("{.*}",h)
    for element in matches:
        key=re.sub("{|}","",element)
        if re.search("video",element):
            key=key.split(".")[1]
            value=emp_dict["video"].get(key,"")
        elif re.search("audio",element):
            key=key.split(".")[1]
            value=emp_dict["audio"].get(key,"")
        elif re.search("images",element):
            key=key.split(".")[1]
            value=emp_dict["images"].get(key,"")
        else:
             value=emp_dict.get(key,"")
        h=re.sub(element,value,h)
    emp_dict["template"]=h

    pprint(emp_dict,width=1)
    check=input("Do you want to Update the yaml: ")
    if check=="Yes" or check=="yes" or check=="Y" or check=="y"  or check=="YES":
        fp=open(yamlpath,"w")
        yaml.dump(emp_dict,fp, default_flow_style=False)
        fp.close() 








