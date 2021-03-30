#!/usr/bin/env python3.6
import argparse
from bs4 import BeautifulSoup
import http.cookiejar
import requests
import subprocess
from pathlib import Path
import json
import os
import pickle
import subprocess
import imageio
from pygifsicle import gifsicle
import shutil
from shutil import which
import math
import configparser
config = configparser.ConfigParser(allow_no_value=True)
import shlex
import json
import pprint
import sys
from consolemenu import SelectionMenu
from threading import Thread
import tempfile
import re
import string
if sys.platform!="win32":
   from simple_term_menu import TerminalMenu

from prompt_toolkit import prompt as input
from prompt_toolkit.completion import WordCompleter

def getBasedName(path):
    basename=subprocess.check_output(['basename',path])

    basename=basename.decode('utf-8')
    if Path(path).is_dir():
        basename=basename[0:-1]
        return basename
    else:
        basename=(os.path.splitext(basename)[0])
        return basename

# function to find the resolution of the input video file
def findVideoMetadata(input,args):
    cmd = f"{args.ffprobe} -v quiet -print_format json -show_format"
    cmd = shlex.split(cmd)
    cmd.append(input)

    cmd2 = f"{args.ffprobe}  -v quiet -print_format json -show_streams"
    cmd2 = shlex.split(cmd2)
    cmd2.append(input)




    # run the ffprobe process, decode create_binary into utf-8 & convert to JSON
    duration = subprocess.check_output(cmd).decode('utf-8')
    duration  = json.loads(duration)['format']['duration']
    t = subprocess.check_output(cmd2).decode('utf-8')
    width=None
    for i in range(0,len(json.loads(t)['streams'])):
        width=json.loads(t)['streams'][i].get('coded_width')
        if width!=None:
            break
    return duration,width




def create_config(args):

    if args.config==None or os.path.exists(args.config)==False:
        print("Could not read config")
        return
    try:
        configpath=args.config
        config.read(configpath)

    except:
        print("Error accessing data from  config")
        return args

    if args.screens==None:
        args.screens=config['general']['screens']
    if args.media==None:
        args.media=config['dirs']['media']
    if args.trackerurl==None:
        args.trackerurl=config['general']['trackerurl']
    if args.password==None:
        args.password=config['general']['password']
    if args.username==None:
        args.username=config['general']['username']
    if args.torrents==None:
        args.torrents=config['dirs']['torrents']
    if args.data==None:
        args.data=config['dirs']['data']
    if args.dottorrent==None:
        args.dottorrent=config['bins']['dottorrent']
    if args.fd==None:
        args.fd=config['bins']['fd']
def fapping_upload(cover,img_path: str) -> str:
    """
    Uploads an image to fapping.sx and returns the image_id to access it
    Parameters
    ----------
    img_path: str
    the path of the image to be uploaded
    Returns
    -------
    str
    """
    # posts the image as a binary file with the upload form
    r = requests.post('https://fapping.empornium.sx/upload.php',files=dict(ImageUp=open(img_path, 'rb')))
    if r.status_code == 200:
        print(r.status_code)
        image=json.loads(r.text)['image_id_public']
        image="https://fapping.empornium.sx/image/" +image
        image=requests.get(image)
        soup = BeautifulSoup(image.text, 'html.parser')
        soup= soup.find('div',{'class' :'image-tools-section thumb_plus_link'})
        inputitem=(soup.find('div',{'class' :'input-item'}).descendants)
        #get bbcode for upload, thumbnails
        link=list(inputitem)
        if(cover==0):
            link=str(link[3]).split()[3][7:-3]
        else:
            link=str(link[3]).split()[3].split(']')[2][0:-5]
            link=link.replace('.th','')
        print(link)
        return link

    else:
        print("Upload Status:",r.status_code,"\n",r.text)
        return None
def create_images(path,dir,args):
    imgstring=""
    count=1
    cover=0
    print("Creating thumbs")
    if os.path.isdir(path):
        os.chdir(path)
        t=subprocess.run([args.fd,'--absolute-path','-e','.mp4','-e','.flv','-e','.mkv','-e','.m4v','-e','.mov','-e','.webm'],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t=t.stdout.decode('utf-8')

#Loop files in Directory
        print("Their are ",len(t.splitlines())," Video Files")
        for line in t.splitlines():
            print("Video Number:" +str(count))
            subprocess.call(['vcsi',line,'-g','3x3','-o',dir,'-w','2880','--quality','92'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            count=count+1

## Files not in Dir

    else:
        os.chdir(dir)
        subprocess.call(['vcsi',path,'-g','3x3','-o',dir,'-w','2880','--quality','92'])

#upload image
    for i, image in enumerate(os.listdir(dir)):
            if i>100:
                print("Max images reached")
                break
            image=dir+image
            upload=fapping_upload(cover,image)
            if upload!=None:
                imgstring=imgstring+upload
#zip or just move images to directory being uplaoded to EMP
    if(count>=100):
        subprocess.call(['7z','a',path+ '/'+ 'thumbnail.zip',dir])
    elif(count>=10):
        photos=path+'/thumbs/'
        photos=photos.replace('//', '/')
        print(photos)
        if os.path.isdir(photos):
            shutil.rmtree(photos)
        shutil.copytree(dir, photos)
    #finalize image string
    imgstring='[spoiler=Thumbs]'+imgstring+'[/spoiler]'
    return imgstring



def createcovergif(path,gifpath,basename,args):
  print("Finding Largest File and Creating gif")
  max=0
  maxfile=path
  upload=None
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
  numframes=0
  reader = imageio.get_reader(maxfile)
  fps = reader.get_meta_data()['fps']
  fps=fps/2
  data=findVideoMetadata(maxfile,args)
  duration=data[0]
  width = int(data[1])
  ##find scale
  startTime=float(duration)
  startTime=math.floor(startTime)*.75
  endTime=startTime+10

  writer = imageio.get_writer(gifpath, fps=fps)
  start=fps*startTime
  end=fps*endTime


  for i,frames in enumerate(reader):
    if i<start:
        continue
    if i%3!=0:
        continue
    if i>end:
        break
    writer.append_data(frames)
  writer.close()
  factor=1
  startloop=True
  while startloop:
    scale=f"--scale={factor}"
    gifsicle(sources=[gifpath],destination=gifpath, optimize=True,options=[scale,"-O3"])
    if os.stat(gifpath).st_size>5000000:
      print(f"File too big at {os.stat(gifpath).st_size} bytes")
      factor=factor*.8
      continue
    startloop=False
  cover=1
  upload=fapping_upload(cover,gifpath)

  try:
    upload=fapping_upload(cover,gifpath)

  except:
    print("Try a different Approved host gif too large/Host Down")
    return
  return upload


def create_torrent(path,torrentpath,args):
   print("Creating torrent")
   torrent=subprocess.run([args.dottorrent,'-p','-t',args.trackerurl,'-s','8M','--exclude',"*.json",path,torrentpath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)



def upload_emp(path,args):
    workingdir=os.path.dirname(os.path.abspath(__file__))
    txtdir=args.data
    myfile=os.path.basename(path)
    myfile=myfile.strip()
    myfile=os.path.splitext(myfile)[0]

    jsonpath=os.path.join(txtdir,f"{myfile}.json")
    username=args.username
    password=args.password
    t=subprocess.run([os.path.join(workingdir,"upload.py"),jsonpath,username,password],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(t.stdout.decode('utf-8'))



def create_binaries(args):
    print("Setting up Binaries")
    workingdir=os.path.dirname(os.path.abspath(__file__))
    if args.dottorrent==None:
        if which("dottorrent")!=None and len(which('dottorrent'))>0:
            args.dottorrent=which('dottorrent')
        else:
            dottorrent=os.path.join(workingdir,"bin","dottorrent")
            args.dottorrent=dottorrent

    if args.fd==None and sys.platform=="linux":
        if len(which('fd'))>0:
            args.fd=which('fd')
        else:
            fd=os.path.join(workingdir,"bin","fd")
            arguments.fd=fd

    if args.fd==None and sys.platform=="win32":
        if len(which('fd.exe'))>0:
            args.fd=which('fd')
        else:
            fd=os.path.join(workingdir,"bin","fd.exe")
            args.fd=fd


    if sys.platform=="linux":
        if which('ffprobe')!=None and len(which('ffprobe'))>0:
            args.ffprobe=which('ffprobe')
        else:
            ffprobe=os.path.join(workingdir,"bin","ffmpeg-unix","ffprobe")
            args.ffprobe=ffprobe
        if which('ffmpeg')!=None and len(which('ffmpeg'))>0:
            args.ffmpeg=which('ffmpeg')
        else:
            ffmpeg=os.path.join(workingdir,"bin","ffmpeg-unix","ffmpeg")
            args.ffmpeg=ffmpeg
    if sys.platform=="win32":
        if which('ffprobe.exe')!=None and len(which('ffprobe.exe'))>0:
            args.ffprobe=which('ffprobe.exe')
        else:
            ffprobe=os.path.join(workingdir,"bin","ffmpeg-win","ffprobe.exe")
            args.ffprobe=ffprobe
        if which('ffmpeg.exe')!=None and len(which('ffmpeg.exe'))>0:
            args.ffmpeg=which('ffmpeg.exe')
        else:
            ffmpeg=os.path.join(workingdir,"bin","ffmpeg-win","ffmpeg.exe")
            args.ffmpeg=ffmpeg
def create_json(path,args):
    jsonpath=None
    basename=getBasedName(path)
    if args.input!=None:
        jsonpath=args.input
    elif args.data!=None:
        jsonpath=os.path.join(args.data,f"{basename}.json")
    else:
        print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")
    createfile="Yes"
    print("Attempting to Create json at ",jsonpath)
    if os.path.isfile(jsonpath):
        createfile=input("File Exist Do you want to overwrite the file? ")
    if createfile!="Yes" and createfile!="yes" and createfile!="y" and createfile!="Y" and createfile!="YES":
        return
    fp=open(jsonpath,"w")
    #open cat.json
    workingdir=os.path.dirname(os.path.abspath(__file__))
    g=open(os.path.join(workingdir,"cat.json"),"r")
    catdict= json.load(g)
    torrentpath=os.path.join(args.torrents,f"{basename}.torrent")
    picdir=os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}/")
    if args.screens!=None:
        picdir=args.screens
    gifpath=os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}.gif")
    try:
        os.mkdir(picdir)
    except Exception as e:
        print(e)
    torrent=Thread(target = create_torrent, args = (path,torrentpath,args))
    torrent.start()
    empdict={}
    sug=re.sub("\."," ",basename)
    sug=string.capwords(sug)
    print("Press Tab for Auto Suggestion\n")
    empdict["Title"]=input("Enter Title: ",completer=WordCompleter([sug],ignore_case=True))
    empdict["Category"]=input("Enter Category: ",completer=WordCompleter(catdict.keys(),ignore_case=True))
    #can we autocomplete tags?
    empdict["Tags"]=input("Enter Tags: ")
    empdict["Description"]=input("Enter Description: ",multiline=True)
    empdict["Cover"]=createcovergif(path,gifpath,basename,args)
    empdict["Images"]=create_images(path,picdir,args)

    torrent.join()
        # release_info.join()
    empdict["Torrent"]=torrentpath
    json.dump(empdict,fp,indent=4)
    fp.close()
    pprint.pprint(empdict,width=1)
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-m','--media')
  parser.add_argument('-t','--torrents')
  parser.add_argument('-s','--screens')
  parser.add_argument('-u','--trackerurl')
  parser.add_argument('-i','--input')
  parser.add_argument('-c','--config')
  parser.add_argument('-d','--data')
  parser.add_argument('-r','--dottorrent')
  parser.add_argument('-f','--fd')
  parser.add_argument('-un','--username')
  parser.add_argument('-pd','--password')
  parser.add_argument('-b','--batch',default=True)
  comd = parser.add_mutually_exclusive_group()
  comd.add_argument('-prepare', action='store_true')
  comd.add_argument('-upload', action='store_true')
  args=parser.parse_args()
  create_config(args)
  create_binaries(args)
  if args.prepare==False and args.upload==False:
    print("you must set -prepare or -upload")
    quit()
  keepgoing = "Yes"
  #setup batchmode
  if os.path.isdir(args.media) and (args.batch==True or  args.batch=="True"):
      choices=sorted(os.listdir(args.media))
      if len(choices)==0:
          print("Upload Folder is Empty")
          quit()


  #single file
  else:
      path=args.media
      if args.prepare:
        print("Prepare Mode\n")
        create_json(path,args)
        keepgoing=input("Prepare Another Upload: ")
      if args.upload:
        print("Upload Mode\n")
        upload_emp(path,args)
        keepgoing=input("Continue Uploading?: ")





  #batchmode
  while keepgoing=="Yes" or keepgoing=="yes" or keepgoing=="Y" or keepgoing=="y"  or keepgoing=="YES":
      if sys.platform!="win32":
          menu = TerminalMenu(choices)
          menu_entry_index = menu.show()
      else:
          menu_entry_index = SelectionMenu.get_selection(choices)


      if menu_entry_index>= (len(choices)):
          quit()
      try:
          path=choices[int(menu_entry_index)]

      except:
          bhdlogger.warn("Please Enter a Valid Value")
          continue
      path=os.path.join(args.media,path)
      if args.prepare:
        print("Prepare Mode\n")
        create_json(path,args)
        keepgoing=input("Prepare Another Upload: ")
      if args.upload:
        print("Upload Mode\n")
        upload_emp(path,args)
        keepgoing=input("Continue Uploading?: ")
