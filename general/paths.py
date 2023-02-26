#! /usr/bin/env python3
import os
import pathlib
import re
import yaml
import tempfile
import glob
import shutil
import natsort
import general.arguments as arguments
import general.console as console
import settings as settings


args=arguments.getargs()
"""
Search for matching files in directory
:param path: path to search
:param filterStr: search query
:param recursive: search for matches recursively
:param dir: search for directories if trues, files if false

:return: list of matching directories
"""
def search(path,filterStr,recursive=False,dir=False,exclude=None,abs=False):
    if exclude==None:
        exclude=[]
    exclude=list(map(lambda x: convertLinux(x),exclude))

    search='**/*'
    if recursive==False:
        search="*"
    
    results=list(map(lambda x:convertLinux(x),glob.glob(str(pathlib.Path(path,search)),recursive=recursive)))
    filteredPaths=list(filter(lambda x:os.path.isdir(x)==dir,results))
    filteredPaths=list(filter(lambda x:not any(re.search(ele,x) for ele in exclude),filteredPaths))
    sortedPaths=natsort.natsorted(filteredPaths)
    return list(filter(lambda x:re.search(filterStr,x)!=None,sortedPaths))
    

def getmediaFiles(inputPath,recursive=True):
    return search(inputPath,"\.mkv|\.mp4",recursive=True)


"""
Generates list of media files/directories files for user to pick

:returns None:
"""

def get_choices():
     files=None
     if os.path.isdir(args.prepare.media):
        files=search(args.prepare.media,".*",recursive=False)
        files.extend(search(args.prepare.media,".*",recursive=False,dir=True))
        return list(map(lambda x:convertLinux(x) ,natsort.natsorted(files)))
     elif os.path.isfile(args.prepare.media):
        return list([convertLinux(args.prepare.media)])
     else:
        console.console.print("No Valid Paths to Process",style="red")
        quit()
"""
Generates basename of path

:param inputPath: path chosen by user
:returns string: basename
"""
def get_upload_name(inputPath):
    return pathlib.Path(inputPath).parts[-1] 

"""
Generates a yml file name

:param inputPath: path chosen by user
:returns str: a yml file path
"""
def generate_yaml(inputPath):
    if inputPath.endswith(".yml") or inputPath.endswith(".yaml"):
        return inputPath
    basename=get_upload_name(inputPath)
    return convertLinux(os.path.join(args.output,f"{basename}.yml"))

"""
Gets all yml files inside directory, Non Recursively

:param inputPath: path chosen by user
:returns array: a array of yml files
"""
def retrive_yaml(inputPath):
    return list(filter(lambda x:re.search(".yml$|\.yaml$",x)!=None,search(inputPath,".*",recursive=True,dir=False)))

"""
Gets empornium categories
:returns catdict:dictionary with categories and id values
"""
def getcat():
    workingdir=settings.workingdir
    g=open(os.path.join(workingdir,"data/cat.yml"),"r")
    return yaml.safe_load(g)

"""
Friendly cross platform version of namedtemporyfile
:returns path: a path to tempfile:
"""

def NamedTemporaryFile(suffix=None):
    file=os.urandom(24).hex()
    if(suffix):
        file=f"{file}{suffix}"
    return os.path.join(settings.tmpdir,file)

"""
Safetly removes file
:returns None:
"""
def remove(input):
    r=pathlib.Path(input)
    if r.is_dir():
        shutil.rmtree(r)
    else:
        r.unlink(missing_ok=True)
"""
convert paths to linux
caused windows paths are annoying
:returns path:converted path
"""       
def convertLinux(path):
    return re.sub(re.escape("\\"), "/", str(pathlib.PurePosixPath(path)))

def rm(input):
    if not input:
        return
    elif pathlib.Path(input).is_dir():
        shutil.rmtree(input,ignore_errors=True)
    else:
        pathlib.Path(input).unlink(missing_ok=True)

def move(send,target):
    if not send or not target:
        return
    if not pathlib.Path(send).exists() or not pathlib.Path(target).parent.exists():
        return
    shutil.move(send,target)
