import os
import subprocess
import shutil
import json
import tempfile
import math
import sys
import zipfile
import re
from pathlib import Path
import xxhash
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

:returns: tuple video data,audio data
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
Finds Videos Recursively, and generates thumbnails for each
Uploads images to host

:param path: directory to scan for video
:param picdir: directory used to store images
:returns uploadstr: returns a string for all images uploaded
"""
def create_images(inputFolder,picdir):
    count=1
   
    console.console.print("Creating screens",style="yellow")
    mediafiles=[inputFolder]
    if os.path.isdir(inputFolder):
        mediafiles=paths.search(inputFolder,"\.mkv|\.mp4",recursive=True)
        
    mtn=mtnHelper()
    for count,file in enumerate(mediafiles): 
        if count==settings.testMaxImagesCount:
            break
        t=subprocess.run([mtn,'-c','3','-r','3','-w','2880','-k','060237','-j','92','-b','2','-f',settings.font,file,'-O',picdir],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if t.returncode==0 or t.returncode==1:
            console.console.print(f"{count+1}. Image created for {file}",style="yellow")
        else:
            print(t.stdout)
            print(t.returncode)
            console.console.print(f"{t.stdout.decode()}\nreturncode:{t.returncode}\nError with mtn",style="red")
    zip_images(inputFolder,picdir)
    imgstr=uploadgalleryHelper(imagesorter(picdir))
    shutil.rmtree(picdir,ignore_errors=True)
    return imgstr

"""
retrives mtn path based on os

:returns mtn:path to mtn binary
"""
def mtnHelper():
    if sys.platform=="linux":
        return settings.mtn_Linux
    return settings.mtn_Windows




    



"""
uploads images to fappening

:param picdir: directory used to store images
:returns: string combined image string for all uploads
"""   
def uploadgalleryHelper(imageList):
    imgstring=""
    for i, image in enumerate(imageList):
            if i>100:
                console.console.print("Max images reached",style="yellow")
                break
            upload=network.fapping_upload(image,msg=True)
            if i<settings.maxNumPostImages and upload!="":
                upload=f"[img={settings.postImageSize}]{upload}[/img]"
                imgstring=f"{imgstring}{upload}"
    return imgstring
"""
Zip images or create  directory or photo storage

:param inputFolder:path to store generated photo storage
:param picdir: directory used to store images

:returns None: 
"""
def zip_images(inputFolder,picdir):
    #zip or just move images to directory being uploaded to EMP
    files=list(Path(picdir).iterdir())
    count=len(files)
    if(count>=100):
        with zipfile.ZipFile(os.path.join(inputFolder,"thumbnail.zip"), mode="w") as archive:
            for filename in files:
                archive.write(filename)
    elif count>=10:
        photos=os.path.join(inputFolder,"screens")
        shutil.rmtree(photos,
        ignore_errors=True)
        shutil.copytree(picdir, photos)



"""
Generates a cover gif using a video file

:param gifpath:gif image path
:param maxfile: File used to generate gif

:returns: imageurl 
"""
def createcovergif(gifpath,maxfile):
    trimedVideo=videoSplitter(maxfile)
    palette=os.path.join(os.path.dirname(trimedVideo),"palette.png")
    console.console.print("Creating GIF",style="yellow")
    subprocess.run(["ffmpeg" ,'-i', trimedVideo,'-filter_complex', '[0:v] palettegen',palette],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    subprocess.run(["ffmpeg" ,'-i', trimedVideo,'-i' ,palette,'-filter_complex', '[0:v] paletteuse',gifpath],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    tempgif=os.path.join(settings.tmpdir, f"{os.urandom(24).hex()}.gif")
    console.console.print("Compressing GIF")
    factor=1
    while True:
        scale=f"--scale={factor}"
        gifsicle(sources=[gifpath],destination=tempgif, optimize=True,options=[scale,"--optimize=3"])
        if os.stat(tempgif).st_size<5000000:
            break
        print(f"File too big at {os.stat(tempgif).st_size/1048576} megabytes\nReducing Size")
        factor=factor*.7 
        
    return network.fapping_upload(tempgif,msg=True,thumbnail=False)
    

"""
finds the Larget File in Directory

:param inputFolder: Directory to scan for video files
:returns: path to selected video file
"""


def find_maxfile(inputFolder):
    files=paths.search(inputFolder,".*",recursive=True)
    media=list(filter(lambda x:re.search("\.mkv|\.mp4",str(x)),files))
    if len(media)==0:
        return None
    fullpaths=list(map(lambda x:str(x),media))
    return list(sorted(fullpaths,key=lambda x:os.path.getsize(x),reverse=True))[0]

"""
Generates a dictionary for static images

:param inputFolder: Directory to scan for video files
:returns: path to selected video file
"""
def createStaticImagesDict(input):
    outdict={}
    for ele in paths.search(input,".*",recursive=True,dir=False):
        outdict[xxhash.xxh32_hexdigest(ele)]={"original":ele,"link":network.fapping_upload(ele)}
    return outdict


def imagesorter(picdir):
    imageList=list(map(lambda x:str(x),Path(picdir).iterdir()))
    return list(sorted(imageList,key=lambda x:getImageSizeHelper(x),reverse=True))

def getImageSizeHelper(filepath):
    data=Image.open(filepath)
    return data.width *data.height

def videoSplitter(maxfile):
    suffix=Path(maxfile).suffixes[-1]
    video,audio=metadata(maxfile)
    duration=video.get("other_duration")/1000
    startTime=math.floor(float(duration))*.75
    endTime=startTime+5
    tempVideoDir=tempfile.mkdtemp(dir=settings.tmpdir)
    tempVideo=os.path.join(tempVideoDir,f"tempvid{suffix}")
    console.console.print(f"Trimming Video from {startTime} secs to {endTime} secs",style="yellow")
    subprocess.run(["ffmpeg","-i",maxfile, "-ss" ,f"{startTime}", "-to", f"{endTime}" ,"-c" ,"copy", tempVideo],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return tempVideo
    
  

  
