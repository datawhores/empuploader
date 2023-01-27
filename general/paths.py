#! /usr/bin/env python3
import os
from pathlib import Path
import re
import yaml
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
def search(path,filterStr,recursive=False,dir=False,exclude=None):
    if exclude==None:
        exclude=[]

    search='**/*'
    if recursive==False:
        search="*"
    
    results=list(map(lambda x:str(x),Path(path).glob(search)))
    filteredPaths=list(filter(lambda x:os.path.isdir(x)==dir,results))
    filteredPaths=list(filter(lambda x:not any(re.search(ele,x) for ele in exclude),filteredPaths))
    sortedPaths=natsort.natsorted(filteredPaths)
    return list(filter(lambda x:re.search(filterStr,x)!=None,sortedPaths))
    

def getmediaFiles(inputFolder,recursive=True):
    return search(inputFolder,"\.mkv|\.mp4",recursive=True)


"""
Generates list of media files/directories files for user to pick

:returns None:
"""

def get_choices():
     files=None
     if os.path.isdir(args.prepare.media):
        files=search(args.prepare.media,".*",recursive=False)
        files.extend(search(args.prepare.media,".*",recursive=False,dir=True))
        return natsort.natsorted(files)
     elif os.path.isfile(args.prepare.media):
        return [args.prepare.media]
     else:
        console.console.print("No Valid Paths to Process",style="red")
        quit()
"""
Generates basename of path

:param inputFolder: path chosen by user
:returns string: basename
"""
def get_upload_name(inputFolder):
    return Path(inputFolder).parts[-1] 

"""
Generates a yml file name

:param inputFolder: path chosen by user
:returns str: a yml file path
"""
def generate_yaml(inputFolder):
    if inputFolder.endswith(".yml") or inputFolder.endswith(".yaml"):
        return inputFolder
    basename=get_upload_name(inputFolder)
    return os.path.join(args.output,f"{basename}.yml")

"""
Gets all yml files inside directory, Non Recursively

:param inputFolder: path chosen by user
:returns array: a array of yml files
"""
def retrive_yaml(inputFolder):
    return list(filter(lambda x:re.search(".yml$|\.yaml$",x)!=None,search(inputFolder,".*",recursive=True,dir=False)))

"""
Gets empornium categories
:returns None:
"""
def getcat():
    workingdir=settings.workingdir
    g=open(os.path.join(workingdir,"data/cat.yml"),"r")
    return yaml.safe_load(g)
"""
Updates system path 

:returns None:
"""
def setPath():
    os.environ["PATH"] = os.pathsep + os.pathsep.join([settings.ffmpeg,settings.gifsicle])