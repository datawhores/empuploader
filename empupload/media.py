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
from pymediainfo import MediaInfo
from PIL import Image
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
def create_images(mediafiles,inputFolder,picdir):
    count=1
    #filter only mediafiles
    mediafiles=list(filter(lambda x: re.search("\.mkv|\.mp4",x),mediafiles))

    console.console.print("Creating screens",style="yellow")
    mtn=mtnHelper()
    for count,file in enumerate(mediafiles): 
        t=subprocess.run([mtn,'-c','3','-r','3','-w','2880','-k','060237','-j','92','-b','2','-f',settings.font,file,'-O',picdir],stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
        if t.returncode==0 or t.returncode==1:
            console.console.print(f"{count+1}. Image created for {file}",style="yellow")
        else:
            console.console.print(t.stdout,style="red")
            console.console.print(t.returncode,style="red")
            console.console.print(f"{t.stdout.decode()}\nreturncode:{t.returncode}\nError with mtn",style="red")
    return zip_images(inputFolder,picdir)


"""
retrives mtn path based on os

:returns mtn:path to mtn binary
"""
def mtnHelper():
    if sys.platform=="linux":
        return shutil.which("mtn") or os.path.join(settings.mtn,"mtn")
    return shutil.which("mtn.exe") or os.path.join(settings.mtn,"windows","mtn.exe")
"""
retrives ffmpeg path based on os

:returns ffmpeg:path to ffmpeg binary
"""
def ffmpegHelper():
    if sys.platform=="linux":
        return shutil.which("ffmpeg") or os.path.join(settings.ffmpeg,"ffmpeg")
    return shutil.which("ffmpeg.exe") or os.path.join(settings.ffmpeg,"ffmpeg.exe")


"""
retrives gifsicle path based on os

:returns gifsicle:path to gifsiclebinary
"""
def gifsicleHelper():
    if sys.platform=="linux":
        return shutil.which("gifsicle") or os.path.join(settings.gifsicle,"gisicle")
    return shutil.which("gifsicle.exe") or os.path.join(settings.ffmpeg,"gifsicle.exe")

    



"""
uploads images to fappening

:param picdir: directory used to store images
:returns: string combined image string for all uploads
"""   
def upload_images(imageList):
    imgstring=""

    for i, image in enumerate(imageList):
            image=paths.convertLinux(image)
            if i>100:
                console.console.print("Max images reached",style="yellow")
                break
            upload=network.fapping_upload(image,msg=True,remove=True)
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
        zipLocation=os.path.join(inputFolder,"thumbnail.zip")
        console.console.print(f"Creating Zip: {zipLocation}")
        with zipfile.ZipFile(zipLocation, mode="w") as archive:
            for filename in files:
                archive.write(filename)
        return [zipLocation]
    elif count>=10:
        photos=os.path.join(inputFolder,"screens")
        console.console.print(f"Creating screens folder: {photos}")
        shutil.rmtree(photos,
        ignore_errors=True)
        shutil.copytree(picdir, photos)
        return paths.search(photos,".*",recursive=False)
    return []



"""
Generates a cover gif using a video file

:param gifpath:gif image path
:param maxfile: File used to generate gif

:returns: imageurl 
"""
def createcovergif(gifpath,maxfile):
    console.console.print(f"Largest File Selected: {maxfile}",style="yellow")
    console.console.print("Starting GIF Process",style="yellow")
    trimedVideo=paths.convertLinux(videoSplitter(maxfile))
    palette=paths.convertLinux(os.path.join(os.path.dirname(trimedVideo),"palette.png"))
    console.console.print("Creating GIF from section",style="yellow")
    ffmpeg=ffmpegHelper()
    proc=subprocess.run([ffmpeg,'-i', trimedVideo,'-filter_complex', f'[0:v] palettegen',palette],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc2=subprocess.run([ffmpeg ,'-i', trimedVideo,'-i' ,palette,'-filter_complex', f'[0:v] paletteuse',gifpath],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    # print(proc.stdout.decode())
    # print(proc.stderr.decode())
    # print(proc.stderr.decode())
    # print(proc2.stderr.decode())
    tempgif=os.path.join(settings.tmpdir, f"{os.urandom(24).hex()}.gif")
    console.console.print("Compressing GIF",style="yellow")
    factor=1
    while True:
        scale=f"--scale={factor}"
        gifsicle=gifsicleHelper()
        gif=subprocess.run([gifsicle, *[scale,"--optimize=3","-lossy=30" ], *[gifpath],  "--output", tempgif],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if os.stat(tempgif).st_size<5000000:
            break
        factor=factor*.7 
        console.console.print(f"File too big at {os.stat(tempgif).st_size/1048576} megabytes\nChanging Scale Factor to {factor}",style="yellow")
    Path(gifpath).unlink(True)
    return network.fapping_upload(tempgif,msg=True,thumbnail=False,remove=True)
    

"""
finds the Larget File in Directory

:param inputFolder: Directory to scan for video files
:returns: path to selected video file
"""


def find_maxfile(media):
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
    if input==None or not Path(input).exists():
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
    fps=float(re.search("[0-9.]*",video.get("frame_rate")).group(0))
    duration=video.get("other_duration")/1000
    startTime=math.floor(float(duration))*(settings.gifStart/100)
    endTime=min(startTime+settings.gifLength,duration)
    tempVideoDir=tempfile.mkdtemp(dir=settings.tmpdir)
    intervid=os.path.join(tempVideoDir,f"inter{suffix}")
    tempVideo=os.path.join(tempVideoDir,f"tempvid{suffix}")
    console.console.print(f"Splitting section of video from {startTime} secs to {endTime} secs",style="yellow")
    ffmpeg=ffmpegHelper()
    proc=subprocess.run([ffmpeg,"-i",maxfile, "-ss" ,f"{startTime}", "-to", f"{endTime}" ,"-c" ,"copy", intervid],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc2=subprocess.run([ffmpeg,"-i",intervid,"-filter:v", f"fps={fps/2}",tempVideo],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    # print(proc.stdout.decode())
    # print(proc.stderr.decode())
    # print(proc.stderr.decode())
    # print(proc2.stderr.decode())
    Path(intervid).unlink()
    return tempVideo

def cleanup(picdir):
    if not args.prepare.picdir:
        shutil.rmtree(picdir,ignore_errors=True)
