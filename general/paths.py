#! /usr/bin/env python3
import os
from pathlib import Path
import re
from InquirerPy import inquirer
import natsort
import general.arguments as arguments
import general.console as console

args=arguments.getargs()
def search(path,filterStr,recursive=False,dir=False):

    search='**/*'
    if recursive==False:
        search="*"
    
    results=map(lambda x:str(x),Path(path).glob(search))
    filteredPaths=list(filter(lambda x:os.path.isdir(x)==dir,results))
    sortedPaths=natsort.natsorted(filteredPaths)
    return list(filter(lambda x:re.search(filterStr,x)!=None,sortedPaths))
    





"""
Check directory is valid for upload
    - at least one file in directory
    - Or file exists on system
:param args: user Commandline/Config arguments
:return: bool returns true if all paremeters are meet
"""
def valid_dir(args):  
    if os.path.isdir(args.media) and len(os.listdir(args.media))==0:
        console.console.print("Upload Folder is Empty",style="red")
        return False
    if os.path.isdir(args.media)==False and os.path.isfile(args.media)==False:
        return False
    return True

"""
Return a list of files

:param args: user Commandline/Config arguments
:returns: Returns a string or list based on type of path for args.media
"""

def getfilesrecursive(path):
 return list(map(lambda x: os.path.join(path,x),os.listdir(path)))

def get_choices():
     if args.prepare.batch:
        return [args.prepare.media]
     elif os.path.isdir(args.prepare.media):
        files=search(args.prepare.media,".*",recursive=False)
        files.extend(search(args.prepare.media,".*",recursive=False,dir=True))
        return natsort.natsorted(files)
     elif os.path.ispath(args.prepare.media):
        return [args.prepare.media]
     else:
        console.console.print("No Valid Paths to Process",style="red")
        quit()
"""
basename of path

:param path: path chosen by user
:returns string: basename
"""
def get_upload_name(path):
    return Path(path).parts[-1] 

"""
retrives yaml files 

:param path: path chosen by user
:returns array: array of paths 
"""
def generate_yaml(path):
    if path.endswith(".yml") or path.endswith(".yaml"):
        return path
    basename=get_upload_name(path)
    return os.path.join(args.output,f"{basename}.yaml")


def retrive_yaml(input):
    return search(input,".*",recursive=True,dir=False)
