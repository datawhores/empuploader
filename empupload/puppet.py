import asyncio
import os
import tarfile
import yaml
import json
from pyppeteer import launch
from pyppeteer import __pyppeteer_home__
import sys
import re
import requests
from shutil import which
import shutil
import tempfile
from tqdm import tqdm
import settings as settings
import runner as runner
import general.console as console
import empupload.network as network

import general.arguments as arguments

args=arguments.getargs()
page=None
dupe=None


"""
Handles Dupes with User Input

:param upload_dict: Options to Embedded in Upload
:param cookie: Cookie For Login

:returns: None
"""
async def run_dupe(upload_dict,cookie):
    print("Searching for Dupes")
    g=open(os.path.join(settings.workingdir,"data/cat.yaml"),"r")
    catdict= yaml.safe_load(g)
    Images=os.path.join(settings.workingdir,"Images")
    url="https://www.empornium.is"
    browser = await launch(executablePath=getChrome(), headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(40000)
    for element in cookie:
        await page.setCookie(element)
    try:
        await page.goto(f'{url}/upload.php')
        inputUploadHandle=await page.querySelector("input[type=file]");
        await inputUploadHandle.uploadFile(upload_dict.get("torrent",""))

        # we need to type the title before checking for dupes , otherwise it fs up
        await page.focus("#title")
        await page.keyboard.type(upload_dict.get("title",""))
        await page.click("#upload_table > table > tbody > tr:nth-child(1) > td:nth-child(2) > span > input[type=submit]")
        #wait for navigation doesn't seem to work
        await page.waitFor(5000);
        element = await page.querySelector("#messagebar")
        msg = await page.evaluate('(element) => element.textContent', element)
    
        if msg!=None and re.search("category|dupes",msg)!=None:
            dupebox= await page.querySelector("#upload_table > div:nth-child(2)")
            dupemsg = await page.evaluate('(dupebox) => dupebox.textContent', dupebox)
            dupemsg= re.sub('\n ', '', dupemsg)
            dupemsg= re.sub(' \n', '', dupemsg)
            dupemsg= re.sub(' +', ' ', dupemsg)
            dupemsg= re.sub('\n+', '\n', dupemsg)
            dupemsg= re.sub('\t+', '*', dupemsg)
            dupemsg=re.sub(" Your file File matched File Size Torrent Files Time Size Uploader ","",dupemsg)
            dupelist=dupemsg.split('\n')

            i=0
            length=len(dupelist)
            #clean up some unneeded data
            while i<length-2:
                dupelist[i]="Your File:"+dupelist[i]
                dupelist[i+1]="File on EMP:"+dupelist[i+1]
                dupelist[i+2]="Conflict Size:"+dupelist[i+2]
                i=i+3
                dupelist.pop(i)
                dupelist.pop(i)
                dupelist[i]="Offending Torrent on Site:"+dupelist[i]
                dupelist[i+1]=" "
                length=length-2
                i=i+2
            dupemsg='\n'.join(dupelist)
            print(dupemsg)
            #print page
            with tempfile.mkstemp() as p:
                await page.waitFor(5000)
                await page.setViewport({ "width": 1920, "height": 2300 })
                await page.screenshot({'path': p[0],'fullPage':True,'type':'jpeg'})
                console.console.print(f"Dupes Screenshot: {network.fapping_upload(p[0])}",style="yellow")
            return True,page
        else:
            console.console.print("No Dupes Found",style="yellow")
            return False,page
    except:
        console.console.print(f"Error Finding Dupes: {network.fapping_upload(p[0])}",style="red")
        quit()


"""
Uploads Torrent to EMP

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload
:param catdict: Categories for EMP

:returns: None
"""

async def run_upload(page,upload_dict):
    g=open(os.path.join(settings.workingdir,"data/cat.yaml"),"r")
    catdict= yaml.safe_load(g)
    Images=os.path.join(settings.workingdir,"Images")
    try:
        await page.click("#upload_table > div.box.pad.shadow.center.rowa > div > input[type=checkbox]")
        await page.focus("#image")
        await page.keyboard.type(upload_dict.get("cover",""))
        await page.focus("#taginput")
        await page.keyboard.type(upload_dict.get("taglist",""))
        await page.focus("#desc")
        if upload_dict.get("template","")!="":
            await page.keyboard.type(upload_dict.get("template",""))
        else:
            await page.keyboard.type(upload_dict.get("desc",""))
            await page.keyboard.press("Enter")
            if upload_dict.get("images","")!=None:
                await page.keyboard.type(upload_dict.get("images",""))
            else:
                await page.keyboard.type(upload_dict.get("thumbs",""))
            await page.keyboard.press("Enter")


        catvalue=catdict.get(upload_dict.get("Category",""),"1")
        await page.select('#category', catvalue)
        await page.click('#post');
        #print page

        uploadimage= os.path.join(Images,f"{randomImageString}_Upload.jpg")
        await page.waitFor(5000)
        await page.setViewport({ "width": 1920, "height": 2300 })
        await page.screenshot({'path': uploadimage,'fullPage':True,'type':'jpeg'})
        print(f"File Should Be Uploaded\nPlease Check {uploadimage}\nIf Upload Not Showing")
    except:
        errorimage= os.path.join(Images,f"{randomImageString}_UploadError.jpg")
        await page.waitFor(5000)
        await page.setViewport({ "width": 1920, "height": 2300 })
        await page.screenshot({'path': errorimage,'fullPage':True,'type':'jpeg'})
        print(f"Error Uploading: {errorimage}")




"""
Uploads Torrent to EMP

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload
:param catdict: Categories for EMP

:returns: None
"""

async def run_preview(page,upload_dict,catdict,randomImageString):
    g=open(os.path.join(settings.workingdir,"data/cat.yaml"),"r")
    catdict= yaml.safe_load(g)
    Images=os.path.join(settings.workingdir,"Images")
    try:
        await page.click("#upload_table > div.box.pad.shadow.center.rowa > div > input[type=checkbox]")
        await page.focus("#image")
        await page.keyboard.type(upload_dict.get("cover",""))
        await page.focus("#taginput")
        await page.keyboard.type(upload_dict.get("taglist",""))
        await page.focus("#desc")
        if upload_dict.get("template","")!="":
            await page.keyboard.type(upload_dict.get("template",""))
        else:
            await page.keyboard.type(upload_dict.get("desc",""))
            await page.keyboard.press("Enter")
            if upload_dict.get("images","")!=None:
                await page.keyboard.type(upload_dict.get("images",""))
            else:
                await page.keyboard.type(upload_dict.get("thumbs",""))
            await page.keyboard.press("Enter")
        catvalue=catdict.get(upload_dict.get("Category",""),"1")
        await page.select('#category', catvalue)
        await page.click('#preview')
        with tempfile.mkstemp() as p:
            await page.waitFor(5000)
            await page.setViewport({ "width": 1920, "height": 2300 })
            await page.screenshot({'path': p[0],'fullPage':True,'type':'jpeg'})
            console.console.print(f"File Preview: {network.fapping_upload(p[0])}",style="yellow")
    except:
        console.console.print("Error Generating Preview",style="red")
        quit()
"""
Runs "find_dupe" with async

:param upload_dict: Options to Embedded in Upload
:param cookie: Cookie For Login

:returns: None
"""
def find_dupe(upload_dict,cookie,randomImageString):
    dupe,page=asyncio.get_event_loop().run_until_complete(run_dupe(upload_dict,cookie,randomImageString))
    return dupe,page

def upload_torrent(page,upload_dict):
    asyncio.get_event_loop().run_until_complete(run_preview(page,upload_dict))

"""
Runs "run_upload" with async

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload
:param catdict: Categories for EMP

:returns: None
"""
def upload_torrent(page,upload_dict):
    asyncio.get_event_loop().run_until_complete(run_upload(page,upload_dict,catdict,randomImageString))

"""
Download Chrome if required on Linux

:param workingdir: Main Directory
:param binfolder: Bin folder in Main Directory


:returns: None
"""
def create_chrome():
  if sys.platform!="linux":
    return
  chromepath=os.path.join(settings.binfolder,"Chrome-Linux")
  if os.path.isfile(os.path.join(chromepath,"chrome"))==False:
    console.console.print("Missing Chrome Install",style="green")
    if os.path.isdir(chromepath):
        shutil.rmtree(chromepath)     
    os.mkdir(chromepath)
    console.console.print(f"Install Chrome to {chromepath}",style="green")
    tempchrome=tempfile.mkdtemp(dir=settings.tmpfile)
    chrome="chrome.tar"
    os.chdir(tempchrome)

    response = requests.get(settings.chromeURL, stream=True,)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    progressBar = tqdm(total=total_size_in_bytes, unit='B',
                        unit_scale=True, unit_divisor=1024)

    with open(chrome, "wb") as fp:
        for data in response.iter_content(block_size):
            fp.write(data)
            progressBar.update(len(data))
    with tarfile.open(chrome) as fp:
        fp.extractall(".")
    os.remove(chrome)
    os.chdir(os.listdir()[0])
    for element in os.scandir():
        shutil.move(element.name, chromepath)
    os.chdir(settings.workingdir)
    shutil.rmtree(tempchrome)
    
def getChrome():
    if sys.platform=="win32":
        chromepath= which("chrome.exe") or which("google-chrome.exe") or os.path.join("C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
    if sys.platform=="linux":
        chromepath=which("google-chrome-stable") or which("google-chrome-beta") or which("google-chrome-dev") or which("chrome")

    if chromepath==None or os.path.exists(chromepath)==False:
            console.console.print("Please install chrome")
            quit()
    return chromepath
    
def loadcookie():
    if args.cookie==None or args.cookie=="":
        print("You need a cookie file")
        quit()
    else:
        g=open(args.cookie,"r")
        args.cookie=json.load(g)