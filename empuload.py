#! /usr/bin/env python3

"""
Usage:
    empupload.py upload <media>
       [--screens=<screens> --torrents=<torrents> --uploadtxt=<uploadtxt> --trackerurl=<trackerurl> --config=<configpath>]
"""


from bs4 import BeautifulSoup
import http.cookiejar
import requests
import subprocess
from docopt import docopt
from pathlib import Path
import json
import os
import pickle
import subprocess
import imageio
from pygifsicle import gifsicle
import shutil
import math
import configparser
config = configparser.ConfigParser()

def getBasedName(path):
    basename=subprocess.check_output(['basename',path])

    basename=basename.decode('utf-8')
    if Path(path).is_dir():
        basename=basename[0:-1]
        return basename
    else:
        basename=(os.path.splitext(basename))
        return basename[0]

def createconfig(arguments,configpath):
        screens=None
        torrents=None
        uploadtxt=None
        trackerurl=None

        if arguments.get('--config')!=None:
            configpath=arguments.get('--config')

        if os.path.isfile(configpath)==True:
            config.read(configpath)
            screens=config['Dirs']['screens']
            torrents=config['Dirs']['torrents']
            uploadtxt=config['Dirs']['uploadtxt']
            trackerurl=config['Dirs']['trackerurl']


        if arguments.get('--screens')!=None:
            screens=arguments.get('--screens')
        if arguments.get('--torrents')!=None:
            torrents=arguments.get('--torrents',torrents)
        if arguments.get('--uploadtxt')!=None:
            uploadtxt=arguments.get('--uploadtxt',uploadtxt)
        if arguments.get('--trackerurl')!=None:
            trackerurl=arguments.get('--trackerurl',trackerurl)
        #check variables
        if screens==None:
            print("Please Enter screens location")
            quit()
        if torrents==None:
            print("Please Enter torrentfile location")
            quit()
        if uploadtxt==None:
            print("Please Enter  location for the uploadtxt file")
            quit()

        if trackerurl==None:
            print("Please Enter  your tracker url")
            quit()
        return[screens,torrents,uploadtxt,trackerurl]


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
    with requests.Session() as s:
        # posts the image as a binary file with the upload form
        r = s.post('https://fapping.empornium.sx/upload.php',
                   files=dict(ImageUp=open(img_path, 'rb')))
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

            return link

        else:
            print('Error occurred during image upload')
            return None
def createimages(path,dir):
    imgstring=""
    count=0
    cover=0
    if Path(path).is_dir():
        os.chdir(path)
        t=subprocess.check_output(['fd','--absolute-path','-e','.mp4','-e','.flv','-e','.mkv'])
        t=t.decode('utf-8')
        os.mkdir(dir)
        os.chdir(dir)
#Loop files in Directory
        for line in t.splitlines():
            count=count+1
            print("Video Number:" +str(count))
            subprocess.call(['vcsi',line,'-g','3x3','-o',dir,'-w','2880','--quality','92'])


## Files not in Dir

    else:
        os.mkdir(dir)
        os.chdir(dir)
        subprocess.call(['vcsi',path,'-g','3x3','-o',dir,'-w','2880','--quality','92'])
        subprocess.call(['vcs','-h','960','-n','9','-c','3','-A','-j',path])
    for image in os.listdir(dir):
            image=dir+image
            upload=fapping_upload(cover,image)
            if upload!=None:
                imgstring=imgstring+upload
    if(count>=100):
        subprocess.call(['7z','a',path+ '/'+ 'image.zip',dir])
    return imgstring

def createDescription(imagelist,basename,uploadtxt):
    txt=uploadtxt + basename+ '.txt'
    desc=""
    with open(txt) as x:
        t=x.readlines()
        for i,line in enumerate(t):
            if i==0:
                title=line
            if i==1:
                tags=line
            if i>1:
                desc=desc+line
    desc=desc+'\n'+'\n' +imagelist
    return[title,tags,desc]



def createcovergif(path,dir,basename,uploadtxt):
  max=0
  maxfile=path
  if Path(path).is_dir():
      os.chdir(path)
      t=subprocess.check_output(['fd','--absolute-path','-e','.mp4','-e','.flv','-e','.mkv'])
      t=t.decode('utf-8')
      for file in t.splitlines():
          temp=os.path.getsize(file)
          if(temp>max):
              max=temp
              maxfile=file
  outputPath = uploadtxt +basename+'.gif'
  numframes=0
  print(f'Convertendo {maxfile} \n em {outputPath}')

  reader = imageio.get_reader(maxfile)
  fps = reader.get_meta_data()['fps']
  fps=(fps/2)
  writer = imageio.get_writer(outputPath, fps=fps)


  for i,frames in enumerate(reader):
    if i<100:
        continue
    if i%3!=0:
        continue
    if i>200:
        break
    # if(numframes%5!=0):
        # continue
    writer.append_data(frames)
    print(f'Quadro {frames} \n')
  print('Terminou!')
  writer.close()
  gifsicle(sources=[outputPath],destination=outputPath, optimize=False, colors=256,options=['--scale=0.4'])
  cover=1
  try:
    upload=fapping_upload(cover,outputPath)

  except:
    print("Try a different Approved host gif too large")
    return
  return upload


def create_torrent(path,basename,trackerurl,torrents):
   torrent=subprocess.check_output(['dottorrent','-p','-t',trackerurl,'-s','8M',path,torrents])
   output= torrents + basename+ '.torrent'
   return output


def create_upload_form(arguments):

#default variables
    path = arguments['<media>']
    basename=getBasedName(path)
    configpath=os.getenv("HOME")+'/.config/empupload.conf'
    config=createconfig(arguments,configpath)
    screens=config[0]
    torrents=config[1]
    uploadtxt=config[2]
    trackerurl=config[3]

    output=uploadtxt + '[EMPOUT]' +   basename+ '.txt'
    dir=screens + basename +'/'
    try:
        shutil.rmtree(dir)
    except:
        pass

    imagelist=createimages(path,dir)
    t=createDescription(imagelist,basename,uploadtxt)
    title=t[0]
    tags=t[1]
    desc=t[2]
    torrent=create_torrent(path,basename,trackerurl,torrents)



    form = {'submit': 'true',
            'Title' :  title,
            'tags'  : tags,
            'Cover' : createcovergif(path,dir,basename,uploadtxt),
            'Description' : desc,
            'Torrent file' : torrent,

            }
    with open(output, 'w') as f:
        for key, value in form.items():
            f.write('%s:%s\n' % (key, value))
    # torrent = {'file_input': open(torrent,'rb')}
    # cookies=login(username,password)
    # print(cookies)
    # print(upload.text)
    # soup = BeautifulSoup(upload.text, 'html.parser')
    # soup2= soup.find_all('div',{'class' :'thin'})
    # print(soup2)
    shutil.rmtree(dir)






if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments['upload']:
        create_upload_form(arguments)
