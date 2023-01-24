import asyncio
import os
import tarfile
import json
import pathlib
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
import general.paths as paths

args=arguments.getargs()



"""
Handles Dupes with User Input

:param upload_dict: Options to Embedded in Upload
:param cookie: Cookie For Login

:returns tuple: return dupe bool, page Object, and a string to dupe fappening upload
"""
async def run_dupe(upload_dict,cookie):
    console.console.print("Searching for Dupes",style="yellow")
    url=settings.empURl
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
        await page.waitFor(10000)
        element = await page.querySelector("#messagebar")
        msg = await page.evaluate('(element) => element.textContent', element)
        p=tempfile.NamedTemporaryFile(suffix=".png")
        #get dupe preview
        await page.waitFor(1000)
        await page.setViewport({ "width": 1920, "height": 2300 })
        await page.screenshot({'path': p.name,'fullPage':True,'type':'jpeg'})
        if msg!=None and re.search("category|dupes",msg)!=None:
            dupemsg=await dupemsgHelper(page)
            return True,page,f"{dupemsg}\nDupes Screenshot: {network.fapping_upload(p.name,thumbnail=False)}"
        else:  
                return False,page,f"Dupes Screenshot: {network.fapping_upload(p.name,thumbnail=False)}"
    except Exception as E:
            console.console.print(f"Error Finding Dupes\n{E}",style="red")
            quit()

"""
Generates msg for found dupes

:param page: Page Object Used to handle request

:returns str: a string with information on dupes
"""

async def dupemsgHelper(page):
    dupebox= await page.querySelector("#upload_table > div:nth-child(2)")
    dupemsg = await page.evaluate('(dupebox) => dupebox.textContent', dupebox)
    dupemsg= re.sub('\n | \n|Your file File matched File Size Torrent Files Time Size Uploader', '', dupemsg)
    dupemsg= re.sub(' +', ' ', dupemsg)
    dupemsg= re.sub('\n+', '\n', dupemsg)
    dupemsg= re.sub('\t+', '*', dupemsg)
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
    return '\n'.join(dupelist) 
    

"""
Uploads Torrent to EMP

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload

:returns: None
"""

async def run_upload(page,upload_dict):
    catdict= paths.getcat()
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
                await page.keyboard.type(upload_dict.get("screens",""))
            await page.keyboard.press("Enter")


        catvalue=catdict.get(upload_dict.get("category",""),"1")
        await page.select('#category', catvalue)
        await page.click('#post')
        p=tempfile.NamedTemporaryFile(suffix=".png")
        await page.waitFor(10000)
        await page.setViewport({ "width": 1920, "height": 2300 })
        await page.screenshot({'path': p.name,'fullPage':True,'type':'jpeg'})
        return f"Upload Screenshot: {network.fapping_upload(p.name,thumbnail=False)}"
    except Exception as E:
        print(f"Error Uploading\n{E}")
    finally:
        await page.close()



"""
Generates preview of upload

:params upload_dict: Options to Embedded in Upload
:params cookie: path to cookie json

:returns str: a string to a fappening post with upload preview
"""

async def run_preview(upload_dict,cookie):
    print("Generating Preview")
    url=settings.empURl
    browser = await launch(executablePath=getChrome(), headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(40000)
    for element in cookie:
        await page.setCookie(element)
    try:
        await page.goto(f'{url}/upload.php')
        # we need to type the title before checking for dupes , otherwise it fs up
        await page.focus("#title")
        await page.keyboard.type(upload_dict.get("title",""))

        await page.focus("#image")
        await page.keyboard.type(upload_dict.get("cover",""))
        await page.click("[name=autocomplete_toggle]")
        await page.focus("#taginput")
        await page.keyboard.type(upload_dict.get("taglist",""))
        await page.waitForSelector("#desc")
        await page.focus("#desc")
        if upload_dict.get("template","")!="":
            await page.keyboard.type(upload_dict.get("template",""))
  
  
        catvalue=paths.getcat().get(upload_dict.get("Category",""),"1")
        await page.select('#category', catvalue)
        p=tempfile.NamedTemporaryFile(suffix=".png")
        await page.click('#post_preview')
        await page.waitFor(10000)
        await page.setViewport({ "width": 1920, "height": 2300 })
        await page.screenshot({'path': p.name,'fullPage':True,'type':'jpeg'})
        return f"File Preview: {network.fapping_upload(p.name,thumbnail=False)}"
    except Exception as E:
        console.console.print(f"Error Generating Preview\n{E}",style="red")
    finally:
        await page.close()

   
 
"""
Runs "find_dupe" with async

:param upload_dict: Options to Embedded in Upload
:param cookie: Cookie For Login

:returns: None
"""
def find_dupe(upload_dict,cookie):
    dupe,page,dupeurl=asyncio.get_event_loop().run_until_complete(run_dupe(upload_dict,cookie))
    return dupe,page,dupeurl

"""
Runs "run_preview" with async

:param upload_dict: Options to Embedded in Upload
:param cookie: Cookie For Login

:returns: None
"""
def create_preview(upload_dict,cookie):
    previewurl= asyncio.get_event_loop().run_until_complete(run_preview(upload_dict,cookie))
    return previewurl

"""
Runs "run_upload" with async

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload

:returns: None
"""
def upload_torrent(page,upload_dict):
    uploadurl=asyncio.get_event_loop().run_until_complete(run_upload(page,upload_dict))
    return uploadurl

"""
Download Chrome if required on Linux

:returns: None
"""
def create_chrome():
  if sys.platform!="linux":
    return
  chromeSystem=settings.chrome_Linux
  if chromeSystem:
    return
  chromepath=os.path.join(settings.binfolder,"chrome_Linux/chrome")
  if os.path.isfile(os.path.join(chromepath,"chrome"))==False:
    chromeDir=str(pathlib.Path(chromepath).parents[0])
    console.console.print("Missing Chrome Install",style="green")
    shutil.rmtree(chromeDir,ignore_errors=True)     
    pathlib.Path(chromeDir).mkdir(parents=True,exist_ok=True)
    console.console.print(f"Install Chrome to {chromepath}",style="green")
    tempchrome=tempfile.mkdtemp(dir=settings.tmpdir)
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
    for element in os.scandir():
        shutil.move(element.name, chromepath)
    os.chdir(settings.workingdir)
    shutil.rmtree(tempchrome)
    return chromepath
    
"""
Get path to chrome passed on system

:returns chrome: path to chrome binary
"""
def getChrome():
    if sys.platform=="win32":
        chromepath= settings.chrome_Windows
    elif sys.platform=="linux":
        chromepath= settings.chrome_Linux
      
           
           
   
"""
loads cookie argument into dicitonary with json parse

:returns cookiedict: dictionary from json cookie file
"""   
def loadcookie():
    if args.cookie==None or args.cookie=="":
        print("You need a cookie file")
        quit()
    else:
        g=open(args.cookie,"r")
        return json.load(g)
        
