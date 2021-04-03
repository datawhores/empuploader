#!/usr/bin/env python3.6
import asyncio
from pyppeteer import launch,element_handle
import os
from pyppeteer import __pyppeteer_home__
import sys
import json
import re
from shutil import which



page=None
dupe=None
async def run_dupe(upload_dict,username,password):
    print("Searching for Dupes")
    workingdir=os.path.dirname(os.path.abspath(__file__))
    chromepath=None
    if  sys.platform=="win32":
        if which("chrome.exe")==None:
            chromepath=os.path.join("C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
        else:
            chromepath=which("google-chrome.exe")

    if sys.platform=="linux":
        if  which("google-chrome-stable")==None:
            chromepath=os.path.join(workingdir,"bin","chrome-Linux")
        else:
            chromepath=which("google-chrome-stable")

    url="https://www.empornium.sx"
    browser = await launch(executablePath=chromepath, headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(40000)
    await page.goto(f'{url}/login')

    await page.keyboard.type(username)
    await page.keyboard.press('Tab')
    await page.keyboard.type(password)
    await page.keyboard.press('Enter')
    await page.waitForNavigation()
    await page.goto(f'{url}/upload.php')
    inputUploadHandle=await page.querySelector("input[type=file]");
    await inputUploadHandle.uploadFile(upload_dict.get("Torrent",""))
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

        t=open("dirty.txt","w")
        dupelist=dupemsg.split('\n')
        i=6
        length=len(dupelist)
        #clean up some unneeded data
        while i<length:
            dupelist.pop(i)
            i=i+6
            length=length-1
        dupemsg='\n'.join(dupelist)
        print(dupemsg)
        print("\n","Order of Matches is Title(matching torrent),File(matching torrent), File(your torrent),Size",flush=True)
        return True,page
    else:
        print("No Dupes")
        return False,page


async def run_upload(page,upload_dict,catdict):
    workingdir=os.path.dirname(os.path.abspath(__file__))

    await page.click("#upload_table > div.box.pad.shadow.center.rowa > div > input[type=checkbox]")
    await page.focus("#image")
    await page.keyboard.type(upload_dict.get("cover",""))
    await page.focus("#taginput")
    await page.keyboard.type(upload_dict.get("tags",""))
    await page.focus("#desc")
    if upload_dict.get("template","")!="":
        await page.keyboard.type(upload_dict.get("template",""))
    else:
        await page.keyboard.type(upload_dict.get("desc",""))
        await page.keyboard.press("Enter")
        await page.keyboard.type(upload_dict.get("Images",""))

    catvalue=catdict.get(upload_dict.get("Category",""),"1")
    await page.select('#category', catvalue)
    await page.click('#post');
    await page.waitFor(10000);
    await page.setViewport({ "width": 1920, "height": 2300 });
    await page.screenshot({'path': os.path.join(workingdir,"final.jpg"),'fullPage':True,'type':'jpeg'})

def find_dupe(upload_dict,username,password):
    dupe,page=asyncio.get_event_loop().run_until_complete(run_dupe(upload_dict,username,password))
    return dupe,page
def upload_torrent(page,upload_dict,catdict):
    asyncio.get_event_loop().run_until_complete(run_upload(page,upload_dict,catdict))
