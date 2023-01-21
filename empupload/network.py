
#! /usr/bin/env python3
import json
import requests
from bs4 import BeautifulSoup
import general.console as console
def fapping_upload(cover,img_path: str) -> str:
    """
    Uploads an image to fapping.sx and returns the image_id to access it
    Parameters

    Thanks to Whoever made this!!!
    I made a few modifications 

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
        console.console.print("Image Uploaded",style="yellow")
        image=json.loads(r.text)['image_id_public']
        image="https://fapping.empornium.sx/image/" +image
        image=requests.get(image)
        soup = BeautifulSoup(image.text, 'html.parser')
        soup= soup.find('div',{'class' :'image-tools-section thumb_plus_link'})
        inputitem=(soup.find('div',{'class' :'input-item'}).descendants)
        #get bbcode for upload, thumbnails
        link=list(inputitem)
        link=str(link[3]).split()[3].split(']')[2][0:-5]
        link=link.replace('.th','')
        console.console.print(link,style="yellow")
        return link

    else:
        print("Upload Status:",r.status_code,"\n",r.text)
        return ""