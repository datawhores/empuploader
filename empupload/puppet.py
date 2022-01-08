#!/usr/bin/env python3.6
import asyncio
from pyppeteer import launch
from pyppeteer import __pyppeteer_home__
import sys
import re
from shutil import which
import empupload.general as general
import subprocess
import shutil
import tempfile
import os


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
    workingdir=general.get_workdir()
    chromepath=None
    if  sys.platform=="win32":
        if which("chrome.exe")==None:
            chromepath=os.path.join("C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
        elif which("google-chrome.exe")!=None:
            chromepath=which("google-chrome.exe")
        else:
            print("Please Install Chrome for Windows")

    if sys.platform=="linux":
        if  which("google-chrome-stable")!=None:
            chromepath=which("google-chrome-stable")
        elif which("chrome")!=None:
            chromepath=which("chrome")
        else:
            print("Please Install Chrome for Linux")
    url="https://www.empornium.is"
    browser = await launch(executablePath=chromepath, headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(40000)
    for element in cookie:
        await page.setCookie(element)

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
        return True,page
    else:
        print("No Dupes")
        return False,page
"""
Uploads Torrent to EMP

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload
:param catdict: Categories for EMP

:returns: None
"""

async def run_upload(page,upload_dict,catdict):
    workingdir=general.get_workdir()
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
    await page.waitFor(10000);
    await page.setViewport({ "width": 1920, "height": 2300 });
    await page.screenshot({'path': os.path.join(workingdir,"final.jpg"),'fullPage':True,'type':'jpeg'})


"""
Runs "find_dupe" with async

:param upload_dict: Options to Embedded in Upload
:param cookie: Cookie For Login

:returns: None
"""
def find_dupe(upload_dict,cookie):
    dupe,page=asyncio.get_event_loop().run_until_complete(run_dupe(upload_dict,cookie))
    return dupe,page

"""
Runs "run_upload" with async

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload
:param catdict: Categories for EMP

:returns: None
"""
def upload_torrent(page,upload_dict,catdict):
    asyncio.get_event_loop().run_until_complete(run_upload(page,upload_dict,catdict))

"""
Download Chrome if required on Linux

:param workingdir: Main Directory
:param binfolder: Bin folder in Main Directory


:returns: None
"""
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