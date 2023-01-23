
#! /usr/bin/env python3
import json
import requests
from bs4 import BeautifulSoup
import general.console as console
def fapping_upload(img_path,cover=False,msg=False):
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
        soup= soup.find('div',{'class' :'image-tools-section thumb_plus_link'})
        inputitem=soup.find('div',{'class' :'input-item'}).descendants
        #get bbcode for upload, thumbnails
        link=list(inputitem)
        link=str(link[3]).split()[3].split(']')[2][0:-5]
        link=link.replace('.th','')
        if msg==True:
            console.console.print("Image Uploaded",style="yellow")
            console.console.print(link,style="yellow")
        return link

    else:
        print(f"Error Uploading\n Status: {r.status_code}\n{r.text}")
        return ""