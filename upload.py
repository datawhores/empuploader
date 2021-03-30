#!/usr/bin/env python3.6
import asyncio
from pyppeteer import launch,element_handle
import os
from pyppeteer import __pyppeteer_home__
import sys
import json
import re
async def main():
    if len(sys.argv)<4:
        print("Missing Argument" )
        return
    f=open(sys.argv[1],"r")
    username=sys.argv[2]
    password=sys.argv[3]
    uploaddict= json.load(f)

    workingdir=os.path.dirname(os.path.abspath(__file__))
    g=open(os.path.join(workingdir,"cat.json"),"r")
    catdict= json.load(g)
    browser = await launch(executablePath='/usr/bin/google-chrome-stable', headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(40000)
    await page.goto('https://www.empornium.is/login')

    await page.keyboard.type(username)
    await page.keyboard.press('Tab')
    await page.keyboard.type(password)
    await page.keyboard.press('Enter')
    await page.waitForNavigation()
    await page.goto('https://www.empornium.is/upload.php')
    inputUploadHandle=await page.querySelector("input[type=file]");
    await inputUploadHandle.uploadFile(uploaddict.get("Torrent",""))
    # we need to type the title before checking for upes , otherwise it fs up
    await page.focus("#title")
    await page.keyboard.type(uploaddict.get("Title",""))
    await page.click("#upload_table > table > tbody > tr:nth-child(1) > td:nth-child(2) > span > input[type=submit]")
    #wait for navigation doesn't seem to work
    await page.waitFor(5000);
    element = await page.querySelector("#messagebar")
    msg = await page.evaluate('(element) => element.textContent', element)
    if msg!=None and re.search("dupe",msg)!=None:
        print("Dupe Found")
        await page.click("#upload_table > div.box.pad.shadow.center.rowa > div > input[type=checkbox]")
    await page.focus("#image")
    await page.keyboard.type(uploaddict.get("Cover",""))
    await page.focus("#taginput")
    await page.keyboard.type(uploaddict.get("Tags",""))
    await page.focus("#desc")
    await page.keyboard.type(uploaddict.get("Description",""))
    await page.keyboard.press("Enter")
    await page.keyboard.type(uploaddict.get("Images",""))

    catvalue=catdict.get(uploaddict.get("Category",""),"1")
    await page.select('#category', catvalue)

    await page.click('#post');
    await page.waitFor(10000);
    await page.setViewport({ "width": 1920, "height": 2300 });
    await page.screenshot({'path': os.path.join(workingdir,"final.jpg"),'fullPage':True,'type':'jpeg'})
    await browser.close()




asyncio.get_event_loop().run_until_complete(main())
