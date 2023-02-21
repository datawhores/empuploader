import asyncio
import json
from playwright.async_api import async_playwright
import re
import os
import shutil
import requests
import tarfile
import tempfile
import pathlib
import settings as settings
import runner as runner
import general.console as console
import empupload.network as network
import general.arguments as arguments
import general.paths as paths
import general.selection as selection
from tqdm import tqdm


args=arguments.getargs()
CHROMEURL="https://github.com/macchrome/linchrome/releases/download/v108.5359.98-M108.0.5359.98-r1016-portable-ungoogled-Lin64/ungoogled-chromium_108.0.5359.98_1.vaapi_linux.tar.xz"


"""
Handles Dupes with User Input

:param upload_dict: Options to Embedded in Upload

:returns tuple: dupe bool and a string to dupe fappening upload
"""
async def run_upload(upload_dict):
    async with async_playwright() as playwright:
        browser = await getbrowserHelper(playwright)
        context = await browser.new_context()
        context.set_default_navigation_timeout(120000) 
        await context.add_cookies(loadcookie())
        page = await context.new_page() 
        dupe,dupestr=await find_dupe(upload_dict,page)
        console.console.print(dupestr,style="yellow")
        if dupe==True and \
        await selection.singleoptions("Ignore dupes and continue upload?",["Yes","No"],sync=False)=="No":
            return "Not Uploaded"
        return await upload(page)

"""
Handles Dupes with User Input

:param upload_dict: Options to Embedded in Upload

:returns tuple: return dupe bool and a string to dupe fappening upload
"""

async def find_dupe(upload_dict,page):
    console.console.print("Searching for Dupes",style="yellow")
    p=paths.NamedTemporaryFile(suffix=".png")
    url=settings.empURl
    try:
        await page.goto(f'{url}/upload.php')
        inputUploadHandle=page.locator("input[type=file]")
        await inputUploadHandle.set_input_files(upload_dict.get("torrent",""))
        await submitBasicInfo(upload_dict,page)
        
        #wait for navigation doesn't seem to work
        await page.click("input[name=checkonly]")
        await page.wait_for_selector("[name=checkonly]",state="detached")
        msgbar= page.locator("#messagebar")
        msg=await msgbar.text_content()
        #get dupe preview
        await page.set_viewport_size({ "width": 1920, "height": 2300 })
        await page.screenshot(path=p,full_page=True)
        if msg==None or re.search("category|dupes",msg)==None:
            return False,f"Dupes Found  False\nDupe Screenshot: {network.fapping_upload(p.name,thumbnail=False,remove=False,msg=False)}"
        else:
            return True,f"\nDupes Found True\n{await dupemsgHelper(page)}\nDupe Screenshot: {network.fapping_upload(p.name,thumbnail=False,remove=False,msg=False)}"
        
    except Exception as E:
            console.console.print(f"Error Finding Dupes\n{E}",style="red")
            quit()
    finally:
        paths.remove(p)

"""
Generates msg for found dupes

:param page: Page Object Used to handle request

:returns str: a string with information on dupes
"""

async def dupemsgHelper(page):
    dupebox= page.locator(".torrent.rowb")
    dupelist = await dupebox.all_text_contents()
    for index,ele in enumerate(dupelist):
        ele= re.sub('\n ', '', ele)
        ele= re.sub(' +', ' ', ele)
        ele= re.sub('\n+', '\n', ele)
        ele= re.sub('\t+', '', ele)
        ele=ele.strip()
        elesplit=list(filter(lambda x:re.fullmatch(" +",x)==None,ele.split("\n")))
        elesplit=list(map(lambda x:x.strip(),elesplit))
        dupelist[index]=\
        f"""
        Your File: {elesplit[0]}
        File on EMP: {elesplit[1]}
        Conflict Size: {elesplit[2]}
        Offending Torrent on Site: {elesplit[3]}
        """
    return '\n\n'.join(dupelist) 
    

"""
Uploads Torrent to EMP

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload

:returns: upload screenshot on fappening
"""

async def upload(page):
    p=paths.NamedTemporaryFile(suffix=".png")
    try:
        ignoredupe=page.locator("input[name=ignoredupes]")
        if await ignoredupe.count()>0:
            await page.click("input[name=ignoredupes]")
        #submit and preview
        await page.click('#post')
        await page.wait_for_selector("#details_top")
        await page.set_viewport_size({ "width": 1920, "height": 2300 })
        await page.screenshot(path=p,full_page=True)
        return f"Upload Screenshot: {network.fapping_upload(p,thumbnail=False,remove=False)}"
    except Exception as E:
        print(f"Error Uploading\n{E}")
    finally:
        paths.remove(p)
        await page.close()
        



"""
Generates preview of upload

:params upload_dict: Options to Embedded in Upload

:returns str: a string to a fappening post with upload preview
"""

async def run_preview(upload_dict):
    print("Generating Preview")
    url=settings.empURl
    async with async_playwright() as playwright:
        browser = getbrowserHelper(playwright)
        context = await browser.new_context()
        await context.add_cookies(loadcookie())
        page = await context.new_page()
        p=paths.NamedTemporaryFile(suffix=".png")
        try:
            await page.goto(f'{url}/upload.php')
            await submitBasicInfo(upload_dict,page)          
            await page.click('#post_preview')
            await page.wait_for_selector(".uploadbody",state="hidden")

            await page.set_viewport_size({ "width": 1920, "height": 2300 })
            await page.screenshot(path=p,full_page=True)
            return f"File Preview: {network.fapping_upload(p,thumbnail=False,msg=False,remove=False)}"
        except Exception as E:
            console.console.print(f"Error Generating Preview\n{E}",style="red")
        finally:
            paths.remove(p)
            await page.close()
"""
Submit some basic information required for uploads
:params upload_dict: Options to Embedded in Upload
:params page: Object representing html page
:returns None:
"""
async def submitBasicInfo(upload_dict,page):
    await page.focus("#title")
    await page.keyboard.type(upload_dict.get("title",""))

    await page.focus("#image")
    await page.keyboard.type(upload_dict.get("cover",""))
    await page.click("[name=autocomplete_toggle]")
    await page.focus("#taginput")
    await page.keyboard.type(upload_dict.get("taglist",""))
    await page.focus("#desc")
    if upload_dict.get("template","")!="":
        await page.keyboard.type(upload_dict.get("template",""))
    else:
        await page.keyboard.type(upload_dict.get("desc",""))
        await page.keyboard.press("Enter")
        await page.keyboard.type(upload_dict.get("screens",""))
        await page.keyboard.press("Enter")
    catvalue=paths.getcat().get(upload_dict.get("category",""),"1")
    select=page.locator("#category")
    await select.select_option(catvalue)
    

 
"""
Runs "run_preview" with async

:param upload_dict: Options to Embedded in Upload

:returns: None
"""
def create_preview(upload_dict):
    previewurl= asyncio.get_event_loop().run_until_complete(run_preview(upload_dict))
    return previewurl

"""
Runs "run_upload" with async

:param page: Page Object Used to handle request
:param upload_dict: Options to Embedded in Upload

:returns: None
"""
def upload_torrent(upload_dict):
    uploadurl=asyncio.get_event_loop().run_until_complete(run_upload(upload_dict))
    return uploadurl

              
"""
loads cookie argument into dicitonary with json parse

:returns cookie array: array of cookies from cookie file
"""   
def loadcookie():
    if args.cookie==None or args.cookie=="":
        print("You need a cookie file")
        quit()
    else:
        g=open(args.cookie,"r")
        return list(map(lambda x:_cookiehelper(x),json.load(g)))
def _cookiehelper(x):
    x.update({"sameSite":"Lax"})
    return x
async def getbrowserHelper(playwright):
    try:
        browsertype= playwright.chromium
        return await browsertype.launch()
    except:
        browsertype= playwright.chromium
        return await browsertype.launch(executable_path=create_chrome())
 
    

"""
Download Chrome if required on Linux
:returns str: str path to installed chrome
"""
def create_chrome():
    if os.name!="posix":
        return
    chromepath=os.path.join(settings.binfolder,"chrome_Linux","chrome")
    if os.path.isfile(os.path.join(chromepath,"chrome"))==False:
        chromeDir=str(pathlib.Path(chromepath).parents[0])
        console.console.print("Missing Chrome Install",style="green")
        shutil.rmtree(chromeDir,ignore_errors=True)     
        pathlib.Path(chromeDir).mkdir(parents=True,exist_ok=True)
        console.console.print(f"Install Chrome to {chromeDir}",style="green")
        tempchrome=tempfile.mkdtemp(dir=settings.tmpdir)
        chrome="chrome.tar"
        os.chdir(tempchrome)

        response = requests.get(CHROMEURL, stream=True,)
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
            shutil.move(element.name, chromeDir)
        os.chdir(settings.workingdir)
        shutil.rmtree(tempchrome)
    os.chmod(chromepath, 0o775)
    return chromepath