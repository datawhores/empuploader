#! /usr/bin/env python3
import argparse
import http.cookiejar
import requests
from bs4 import BeautifulSoup
import requests
import subprocess
import yaml
import json
import os
import imageio
from pygifsicle import gifsicle
import shutil
from shutil import which
import math
import configparser
config = configparser.ConfigParser(allow_no_value=True)
import sys
from threading import Thread
import tempfile
import re
import string
from pprint import pprint
from pymediainfo import MediaInfo
if sys.platform=="win32":
    from consolemenu import SelectionMenu
if sys.platform!="win32":
   from simple_term_menu import TerminalMenu
from prompt_toolkit import prompt as input
from prompt_toolkit.completion import WordCompleter
from upload import find_dupe,upload_torrent

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
    if args.screens==None and config['general']['screens']!=None and len(config['general']['screens'])!=0:
        args.screens=config['general']['screens']
    if args.template==None and config['general']['template']!=None and len(config['general']['template'])!=0:
        args.template=config['general']['template']
    if args.font==None and config['general']['font']!=None and len(config['general']['font'])!=0:
        args.font=config['general']['fonts']
    if args.media==None and config['dirs']['media']!=None and len(config['dirs']['media'])!=0:
        args.media=config['dirs']['media']
    if args.trackerurl==None and config['general']['trackerurl']!=None and len(config['general']['trackerurl'])!=0:
        args.trackerurl=config['general']['trackerurl']
    if args.cookie==None and config['general']['cookie']!=None and len(config['general']['cookie'])!=0:
        args.cookie=config['general']['cookie']
    if args.torrents==None and config['dirs']['torrents']!=None and len(config['dirs']['torrents'])!=0:
        args.torrents=config['dirs']['torrents']
    if args.data==None and config['dirs']['data']!=None and len(config['dirs']['data'])!=0:
        args.data=config['dirs']['data']
    if args.images==None and config['dirs']['images']!=None and len(config['dirs']['images'])!=0:
        args.images=config['dirs']['data']
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
        return ""
def find_maxfile(path):
    print("Finding Largest File for Metadata/Covers")
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

def create_images(path,picdir,args):
    imgstring=""
    count=1
    cover=0
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
#upload image
    for i, image in enumerate(os.listdir(picdir)):
            if i>100:
                print("Max images reached")
                break
            image=picdir+image
            upload=fapping_upload(cover,image)
            imgstring=imgstring+upload
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
    return imgstring

def set_template_img(args):
    images={}
    if args.images==None:
        return
    if os.path.isdir(args.images)==False:
        print("Please Provide a valid argument to args.images")
    os.chdir(args.images)
    t=subprocess.run([args.fd,'--absolute-path','-t','f'],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t=t.stdout.decode('utf-8')
    print("Adding Images from your Imagedir to YAML")
    for line in t.splitlines():
        basename=os.path.basename(line)
        link=fapping_upload(1,line)
        images[basename]=link
    return images


def createcovergif(maxfile,gifpath,basename,args):
  if args.cover!=None:
      gifpath=args.cover
      print("Using Predetermined Path")
  else:
      print("Creating Cover GIF")
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
      while startloop:
        scale=f"--scale={factor}"

        gifsicle(sources=[gifpath],destination=tempgif, optimize=True,options=[scale])
        if os.stat(tempgif).st_size>5000000:
          print(f"File too big at {os.stat(tempgif).st_size} bytes\nReducing Size")
          factor=factor*.7
          continue
        startloop=False
  try:
    upload=fapping_upload(1,tempgif)

  except:
    print("Try a different Approved host gif too large/Host Down")
    return
  return upload


def create_torrent(path,torrentpath,args):
   print("Creating torrent")
   torrent=subprocess.run([args.dottorrent,'-p','-t',args.trackerurl,'-s','8M','--exclude',"*.yaml",path,torrentpath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)



def upload_emp(path,args):
    workingdir=os.path.dirname(os.path.abspath(__file__))
    upload=None
    basename=os.path.basename(path)

    if os.path.isfile(basename):
        basename=os.path.splitext(basename)[:-1]

    if args.input!=None:
        yamlpath=args.input
    elif args.data!=None:
        yamlpath=os.path.join(args.data,f"{basename}.yaml")
    else:
        print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")
        quit()
    f=open(yamlpath,"r")
    upload_dict= yaml.load(f)
    g=open(os.path.join(workingdir,"cat.yaml"),"r")
    catdict= yaml.load(g)

    cookie=None
    if args.cookie==None or args.cookie=="":
        print("You need a cookie file")
        quit()
    else:
        g=open(args.cookie,"r")
        cookie=json.load(g)

    dupe,page=find_dupe(upload_dict,cookie)

    if dupe==True:
        upload=input("Ignore dupes and continue upload?: ")
    if dupe==False or upload=="Yes" or upload=="YES" or upload=="Y" or upload=="y" or upload=="YES":
        upload_torrent(page,upload_dict,catdict)

#alternative requests system if we ever get it working
# def upload_emp(path,args):
#     workingdir=os.path.dirname(os.path.abspath(__file__))
#     upload=None
#     txtdir=args.data
#     basename=os.path.basename(path)
#     if os.path.isfile(basename):
#         basename=os.path.splitext(basename)[:-1]
#     if args.input!=None:
#         jsonpath=args.input
#     elif args.data!=None:
#         jsonpath=os.path.join(args.data,f"{basename}.json")
#     else:
#         print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")
#     f=open(jsonpath,"r")
#     upload_dict= json.load(f)
#     #change some of the keys
#     if upload_dict.get("template","")!="":
#         upload_dict["desc"]=upload_dict.get("template","")
#     upload_dict.pop("template")
#     upload_dict["submit"]='true'
#     upload_dict["MAX_FILE_SIZE"]=2097152
#     upload_dict["anonymous"]=0
#     url="https://www.empornium.is/upload.php"
#     s = requests.Session()
#
#     cookie = http.cookiejar.MozillaCookieJar(args.cookie)
#     cookie.load()
#     print(cookie)
#     print(type(cookie))
#     quit()
#     #get auth token
#     t=s.get(url,cookies=cookie)
#     auth=re.search("var authkey.*;",t.text).group()
#     auth=re.sub("var authkey = ","",auth)
#     auth=re.sub(";" ,"",auth)
#     auth=re.sub("\"" ,"",auth)
#     print(auth)
#     upload_dict["auth"]=auth
#     myfiles = {'file_input': open(upload_dict.get("torrent","") ,'rb')}
#     t=s.post(url,cookies=cookie,data=upload_dict,files=myfiles)
#     # print(t.text)
#     t=s.get(url,cookies=cookie)
#     print(t.text)
#     print("one")
    #

    # #check if dupe
    # upload_dict["ignoredupes"]="on"
    # t=s.post(url,cookies=cookie,data=upload_dict,files=myfiles)
    # print(t.text)
    # t=s.post(url,cookies=cookie,header=header)
    # #get auth token if no dupe submit
    # t=s.post(url,cookies=cookie,header=header)


#     g=open(os.path.join(workingdir,"cat.json"),"r")
#     catdict= json.load(g)
#     username=args.username
#     password=args.password
#     dupe,page=find_dupe(upload_dict,username,password)
#
#     if dupe==True:
#         upload=input("Ignore dupes and continue upload?: ")
#     if dupe==False or upload=="Yes" or upload=="YES" or upload=="Y" or upload=="y" or upload=="YES":
#         upload_torrent(page,upload_dict,catdict)

def create_chrome(workingdir,binfolder):
  chromepath=os.path.join(binfolder,"Chrome-Linux")
  if os.path.isfile(os.path.join(chromepath,"chrome"))==False:
      if os.path.isdir(chromepath):
          shutil.rmtree(chromepath)
      os.mkdir(chromepath)
      tempchrome=os.path.join(tempfile.gettempdir(), f"{os.urandom(24).hex()}/")
      os.mkdir(tempchrome)
      os.chdir(tempchrome)

      subprocess.run(["wget","https://github.com/macchrome/linchrome/releases/download/v90.0.4430.93-r857950-portable-ungoogled-Lin64/ungoogled-chromium_90.0.4430.93_1.vaapi_linux.tar.xz"])
      subprocess.run(["tar","xf","ungoogled-chromium_90.0.4430.93_1.vaapi_linux.tar.xz"])
      os.remove("ungoogled-chromium_90.0.4430.93_1.vaapi_linux.tar.xz")
      c=os.listdir()[0]

      os.chdir(c)
      for element in os.scandir():
          shutil.move(element.name, chromepath)
      os.chdir(workingdir)

def create_binaries(args):
    print("Setting up Binaries")
    workingdir=os.path.dirname(os.path.abspath(__file__))

    if args.font==None:
        args.font=os.path.join(workingdir,"bin","mtn","OpenSans-Regular.ttf")

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
        if which('mtn')!=None and len(which('mtn'))>0:
            args.mtn=which('mtn')
        else:
            mtn=os.path.join(workingdir,"bin","mtn","mtn")
            args.mtn.exe=mtn
        if which('fd')!=None and len(which('fd'))>0:
            args.fd=which('fd')
        else:
            fd=os.path.join(workingdir,"bin","fd")
            args.fd=fd

        if which("dottorrent")!=None and len(which('dottorrent'))>0:
            args.dottorrent=which('dottorrent')
        else:
            dottorrent=os.path.join(workingdir,"bin","dottorrent")
            args.dottorrent=dottorrent
    elif sys.platform=="win32":
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
        if which('mtn.exe')!=None and len(which('mtn.exe'))>0:
            args.mtn=which('mtn.exe')
        else:
            mtn=os.path.join(workingdir,"bin","mtn","mtn.exe")
            args.mtn.exe=mtn
        if which('fd.exe')!=None and len(which('fd.exe'))>0:
            args.fd=which('fd.exe')
        else:
            fd=os.path.join(workingdir,"bin","fd.exe")
            args.fd=fd
        if which("dottorrent.exe")!=None and len(which('dottorrent'))>0:
            args.dottorrent=which('dottorrent')
        else:
            dottorrent=os.path.join(workingdir,"bin","dottorrent.exe")
            args.dottorrent=dottorrent
def create_yaml(path,args):
    yamlpath=None
    maxfile=find_maxfile(path)
    video,audio=metadata(maxfile)
    basename=os.path.basename(path)
    if os.path.isfile(basename):
        basename=os.path.splitext(basename)[:-1]
    if args.input!=None:
        yamlpath=args.input
    elif args.data!=None:
        yamlpath=os.path.join(args.data,f"{basename}.yaml")
    else:
        print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")
    createfile="Yes"
    print("\nAttempting to Create yaml at",yamlpath)
    if os.path.isfile(yamlpath):
        createfile=input("File Exist Do you want to overwrite the file? ")
    if createfile!="Yes" and createfile!="yes" and createfile!="y" and createfile!="Y" and createfile!="YES":
        return
    fp=open(yamlpath,"w")
    #open cat.json
    workingdir=os.path.dirname(os.path.abspath(__file__))
    g=open(os.path.join(workingdir,"cat.yaml"),"r")
    catdict= yaml.load(g)
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
    emp_dict["cover"]=createcovergif(maxfile,gifpath,basename,args)
    emp_dict["thumbs"]=create_images(path,picdir,args)
    emp_dict["audio"]=audio
    emp_dict["video"]=video
    emp_dict["images"]=set_template_img(args)
    matches=[]
    h=""
    if args.template!=None and os.path.isfile(args.template):
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
    torrent.join()
    emp_dict["torrent"]=torrentpath
    yaml.dump(emp_dict,fp, default_flow_style=False)
    fp.close()
    pprint(emp_dict,width=1)
def update_template(path,args):
    #open current file
    basename=os.path.basename(path)
    if os.path.isfile(basename):
        basename=os.path.splitext(basename)[:-1]
    if args.input!=None:
        yamlpath=args.input
    elif args.data!=None:
        yamlpath=os.path.join(args.data,f"{basename}.yaml")
    else:
        print("You must enter a folder to save data to with --data options\n Alternatively you can put a direct path with --input")

    f=open(yamlpath,"r")
    emp_dict= yaml.load(f)
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
    emp_dict["Template"]=h

    pprint(emp_dict,width=1)
    check=input("Do you want to Update the yaml: ")
    if check=="Yes" or check=="yes" or check=="Y" or check=="y"  or check=="YES":
        fp=open(yamlpath,"w")
        yaml.dump(emp_dict,fp, default_flow_style=False)
        fp.close()
if __name__ == '__main__':
    #setup path
  workingdir=os.path.dirname(os.path.abspath(__file__))
  binfolder=os.path.join(workingdir,"bin")
  binlist=[]
  t=os.listdir(binfolder)
  for path in t:
      full=os.path.join(binfolder,path)
      if os.path.isdir(full) and full not in os.environ["PATH"]:
          binlist.append(full)
  os.environ["PATH"] += os.pathsep + os.pathsep.join(binlist)
  parser = argparse.ArgumentParser()
  parser.add_argument('-m','--media')
  parser.add_argument('-t','--torrents')
  parser.add_argument('-s','--screens')
  parser.add_argument('-cv','--cover')
  parser.add_argument('-g','--images')
  parser.add_argument('-tm','--template')
  parser.add_argument('-u','--trackerurl')
  parser.add_argument('-i','--input')
  parser.add_argument('-c','--config')
  parser.add_argument('-d','--data')
  parser.add_argument('-f','--font')
  parser.add_argument('-k','--cookie')
  parser.add_argument('-b','--batch',default=True)
  comd = parser.add_mutually_exclusive_group()
  comd.add_argument('-prepare', action='store_true')
  comd.add_argument('-upload', action='store_true')
  comd.add_argument('-update', action='store_true')
  comd.add_argument('-createtor', action='store_true')
  args=parser.parse_args()
  create_config(args)
  create_binaries(args)



  if args.prepare==False and args.upload==False and args.update==False and args.createtor==False:
    print("you must set -prepare or -upload or -update or -createtor")
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
        create_yaml(path,args)
        keepgoing=input("Prepare Another Upload: ")
      if args.upload:
        print("Upload Mode\n")
        upload_emp(path,args)
        keepgoing=input("Continue Uploading?: ")
      if args.update:
        print("Update Template Mode\n")
        update_template(path,args)
        keepgoing=input("Update Another Template?: ")





  #batchmode
  while keepgoing=="Yes" or keepgoing=="yes" or keepgoing=="Y" or keepgoing=="y"  or keepgoing=="YES":
      if sys.platform!="win32":
          menu = TerminalMenu(choices)
          menu_entry_index = menu.show()
      else:
          menu_entry_index = SelectionMenu.get_selection(choices)

      if menu_entry_index>= (len(choices)):
          continue
      try:
          path=choices[int(menu_entry_index)]

      except:
          bhdlogger.warn("Please Enter a Valid Value")
          continue
      path=os.path.join(args.media,path)
      #crete basename for some modes
      basename=os.path.basename(path)
      if os.path.isfile(basename):
          basename=os.path.splitext(basename)[:-1]
      if args.prepare:
        print("Prepare Mode\n")
        create_yaml(path,args)
        keepgoing=input("Prepare Another Upload: ")
      if args.upload:
        print("Upload Mode\n")
        create_chrome(workingdir,binfolder)
        upload_emp(path,args)
        keepgoing=input("Continue Uploading?: ")
      if args.update:
        print("Update Template Mode\n")
        update_template(path,args)
        keepgoing=input("Update Another Template: ")
      if args.createtor:
        print("Torrent Creator Mode\n")
        torrentpath=os.path.join(args.torrents,f"{basename}.torrent")
        create_torrent(path,torrentpath,args)
        keepgoing=input("Continue Making Torrents: ")
