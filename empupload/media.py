#! /usr/bin/env python3
from pymediainfo import MediaInfo
import empupload.network as network
import os
import subprocess
import shutil
import json
import empupload.general as general

import math
import imageio
from pygifsicle import gifsicle
import tempfile



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
def create_images(path,picdir,args):
    count=1
    print("Creating thumbs")
    #files in directory
    if os.path.isdir(path):
        os.chdir(path)
        t=subprocess.run([args.fd,'--absolute-path','-e','.mp4','-e','.flv','-e','.mkv','-e','.m4v','-e','.mov','-e','.webm'],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t=t.stdout.decode('utf-8')
#Loop files in Directory
        print("Their are ",len(t.splitlines())," Video Files")
        for line in t.splitlines():
            print("Video Number:" +str(count))
            subprocess.call([args.mtn,'-c','3','-r','3','-w','2880','-j','92','-b','2','-f',args.font,line,'-O',picdir],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            count=count+1
## Files not in Dir
    else:
        subprocess.call([args.mtn,'-c','3','-r','3','-w','2880','-j','92','-b','2','-f',args.font,path,'-O',picdir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    zip_images(count,path,picdir)
    return upload_image(picdir)
"""
uploads images to fappening

:param picdir: directory used to store images
:returns: string imagestring with urls
"""   
def upload_image(picdir):
    imgstring=""
    for i, image in enumerate(os.listdir(picdir)):
            if i>100:
                print("Max images reached")
                break
            image=picdir+image
            upload=network.fapping_upload(False,image)
            cover=False
            imgstring=imgstring+upload
    return imgstring
"""
Move Files To Final Destionation for upload

:param count:Number of files 
:param path: path chosen by user
:param picdir: directory used to store images

:returns: tuple video,audio data
"""
def zip_images(count,path,picdir):
    #zip or just move images to directory being uploaded to EMP
    if(count>=100):
        zipfile=os.path.join(path,"thumbnail.zip")
        if os.path.isfile(zipfile):
            os.remove(zipfile)
        subprocess.call(['7z','a',zipfile,picdir])
    elif count>=10:
        photos=os.path.join(path,"thumbs")
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
def createcovergif(gifpath,maxfile,args):
    if args.cover!=None:
      gifpath=args.cover
      print("Using Predetermined Path")
    else:
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
      print("Generating GIF")
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
      print("Compressing GIF")
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


def find_maxfile(path,args):
    max=0
    maxfile=path
    if os.path.isdir(path):
        os.chdir(path)
        t=subprocess.run([args.fd,'--absolute-path','-e','.mp4','-e','.flv','-e','.mkv','-e','.m4v','-e','.mov','-e','.webm'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t=t.stdout.decode('utf-8')
        if len(t)==0:
          return "No Video Files for gif creation"
        for file in t.splitlines():
            temp=os.path.getsize(file)
            if(temp>max):
                max=temp
                maxfile=file
    return maxfile



