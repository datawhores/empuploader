
#! /usr/bin/env python3
import json
import requests
import re
from bs4 import BeautifulSoup
import general.console as console
import settings as settings
def fapping_upload(img_path,thumbnail=True,msg=False):
    """
    Uploads an image to fapping.sx and returns the image_id to access it
    Parameters

    Thanks to Whoever made this!!!
    I made a few modifications 


     :parmas img_path: path of image to be uploaded
     :parmas cover: a bool for whether this is a cover imageath of image to be uploaded, errors are always printed
     :params msg: a bool on whether to print succesful upload msg
    
    """
    # posts the image as a binary file with the upload form
    r = requests.post('https://fapping.empornium.sx/upload.php',files=dict(ImageUp=open(img_path, 'rb')))
    if r.status_code == 200:
        image=json.loads(r.text)['image_id_public']
        image="https://fapping.empornium.sx/image/" +image
        image=requests.get(image)
        soup = BeautifulSoup(image.text, 'html.parser')
        list=soup.find_all("input")
        #get bbcode for upload, thumbnails
        link=None
        if thumbnail:
            link=list[3]["value"]
            printmsgHelper(link,msg)
            return link
    
        else:
            link= soup.find_all("input")[1]["value"]
            printmsgHelper(link,msg)
            return link



    else:
        print(f"Error Uploading\n Status: {r.status_code}\n{r.text}")
        return ""

def printmsgHelper(link,msg):
    if msg==True:
        console.console.print("Image Uploaded",style="yellow")
        console.console.print(link,style="yellow")