#! /usr/bin/env python3
import os
import subprocess
import shutil
import json
import tempfile
import math
from pathlib import Path
import re
import imageio
from pygifsicle import gifsicle
from pymediainfo import MediaInfo
import general.arguments as arguments
import empupload.network as network
import runner as runner
import general.console as console
import settings as settings
import general.paths as paths


args=arguments.getargs()



"""
Returns media_info for video and audio track

:param path: path chosen by user

:returns: tuple video,audio data
"""
def metadata(path):
    media_info = MediaInfo.parse(path)
    media_info2 = MediaInfo.parse(path,full=False)
    media_info=json.loads(media_info.to_json())["tracks"]
    media_info2=json.loads(media_info2.to_json())["tracks"]
    video=None
    audio=None
    for i in range(0,len(media_info)):
        if media_info[i].get("track_type") == "Video":
            media_info2[i]["other_duration"]=media_info[i]["duration"]
            media_info2[i]["other_width"]=media_info[i]["width"]
            media_info2[i]["other_height"]=media_info[i]["height"]
            video=media_info2[i]
        if media_info[i].get("track_type") == "Audio":
            audio=media_info2[i]
    return video,audio


"""
Creates Images in picdir

:param path: path chosen by user
:param picdir: directory used to store images
:param args: user Commandline/Config arguments
:returns: tuple video,audio data
"""
def create_images(input,picdir):
    count=1
   
    console.console.print("Creating Thumbs",style="yellow")
    mediafiles=[input]
    if os.path.isdir(input):
        mediafiles=paths.search(input,"\.mkv|\.mp4",recursive=True)
        
        

    #get rid of mtn if possibl
    for count,file in enumerate(mediafiles):   
        print([settings.mtn,'-c','3','-r','3','-w','2880','-k','060237','-j','92','-b','2','-f',settings.font,file,'-O',picdir])
        subprocess.call([settings.mtn,'-c','3','-r','3','-w','2880','-k','060237','-j','92','-b','2','-f',settings.font,file,'-O',picdir],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    zip_images(count,input,picdir)
    return upload_images(picdir)
"""
uploads images to fappening

:param picdir: directory used to store images
:returns: string imagestring with urls
"""   
def upload_images(picdir):
    imgstring=""
    for i, image in enumerate(os.listdir(picdir)):
            if i>100:
                console.console.print("Max images reached",style="yelow")
                break
            image=os.path.join(picdir,image)
            upload=network.fapping_upload(False,image)
            imgstring=imgstring+upload
    return imgstring
"""
Move Files To Final Destionation for upload

:param count:Number of files 
:param path: path chosen by user
:param picdir: directory used to store images

:returns: tuple video,audio data
"""
def zip_images(count,input,picdir):
    #zip or just move images to directory being uploaded to EMP
    if(count>=100):
        zipfile=os.path.join(input,"thumbnail.zip")
        Path.unlink(zipfile,missing_ok=True)
        subprocess.call(['7z','a',zipfile,picdir])
    elif count>=10:
        photos=os.path.join(input,"thumbs")
        print(photos)
        if os.path.isdir(photos):
            shutil.rmtree(photos)
        shutil.copytree(picdir, photos)


"""
Move Files To Final Destionation for upload

:param gifpath:gif image path
:param basename: basename of path chosen by user
:param args: user Commandline/Config arguments

:returns: imageurl 
"""
def createcovergif(gifpath,maxfile):
    numframes=0
    video,audio=metadata(maxfile)
    duration=video.get("other_duration")/1000
    width = video.get("other_width")
    reader = imageio.get_reader(maxfile)
    fps = reader.get_meta_data()['fps']
    writer = imageio.get_writer(gifpath, fps=fps/2)
    startTime=float(duration)
    startTime=math.floor(startTime)*.75
    start=fps*startTime
    endTime=startTime+5
    end=fps*endTime
    console.console.print("Generating GIF",style="yellow")
    for i ,frames in enumerate(reader):
        if i<start or i%3!=0:
            continue
        if i>end:
            break
        writer.append_data(frames)
    writer.close()

    factor=1
    startloop=True
    tempgif=os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}.gif")
    console.console.print("Compressing GIF")
    while startloop:
        scale=f"--scale={factor}"
        gifsicle(sources=[gifpath],destination=tempgif, optimize=True,options=[scale])
        if os.stat(tempgif).st_size>5000000:
          print(f"File too big at {os.stat(tempgif).st_size} bytes\nReducing Size")
          factor=factor*.7
          continue
        startloop=False
    try:
        upload=network.fapping_upload(True,tempgif)
    except:
        print("Try a different Approved host gif too large/Host Down")
        return
    return upload

"""
finds the Larget File in Directory

:param args: user Commandline/Config arguments
:param path: path chosen by user

:returns: path as string
"""


def find_maxfile(input):
    files=Path(input).glob('**/*')
    media=list(filter(lambda x:re.search("\.mkv|\.mp4",str(x)),files))
    if len(media)==0:
        return None
    fullpaths=list(map(lambda x:str(x),media))
    return list(sorted(fullpaths,key=lambda x:os.path.getsize(x),reverse=True))[0]
    

"""
generates random Prefix

:param arguments: arguments passed by template

:returns: randomized prefix string
"""  
    
def set_template_img():
    images={}
    if args.prepare.images==None:
        return
    
    if os.path.isdir(args.prepare.images)==False:
        console.console.print("Image Path is not dir",style="red")
        return
    files=Path(args.prepare.images).glob('**/*')
    fullpaths=list(map(lambda x:str(x),files))
    console.console.print("Adding Images from your Imagedir to YAML",style="yellow")
    for file in fullpaths:
        basename=paths.get_upload_name(file)
        images[basename]=network.fapping_upload(False,file)
    return images     
"""
Creates Images Folder

:param workingdir: main directory of program

:returns: None
"""


def createImages(workingdir):
    Images=os.path.join(workingdir,"Images")
    if os.path.isdir(Images)==False:
        os.mkdir(Images)
 

def createStaticImagesDict(input):
    return _imagesDictHelper(input)[_baseNameHelper(input)]


def _imagesDictHelper(input):
    outdict={}
    inputKey=os.path.basename(input).lower()
    outdict[inputKey]={}
    for ele in paths.search(input,".*",recursive=False,dir=True) :
        outdict[inputKey][_baseNameHelper(ele)]=_imagesDictHelper(ele)
    for ele in paths.search(input,".*",recursive=False,dir=False):
        outdict[inputKey][_baseNameHelper(ele)]=network.fapping_upload(False,ele)
    return outdict

def _baseNameHelper(input):
    return re.sub("\..*","",os.path.basename(input).lower())
    


