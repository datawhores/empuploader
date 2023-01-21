This script automates the process of uploading

https://github.com/excludedBittern8/empuploader/wiki/Uploading-Torrents


# Requirements

> - Python 3.6 or higher


# Install

## Repo
- git clone https://github.com/excludedBittern8/empuploader
- cd empuploader

## Python

### Linux

* python3 -m pip install --user virtualenv
* python3 -m venv env
* source env/bin/activate
* which python -> should be the virtualenv
* pip3 install -r requirements.txt
* pip install imageio[ffmpeg]
* deactivate -> Do this after installing the requirements


### Windows
* git clone ​
* py -3 -m pip install --user virtualenv
* py -3 -m venv env
* .\env\Scripts\activate
* which python -> should be the virtualenv
* py -m pip install -r requirements.txt
* pip install imageio[ffmpeg]
* deactivate -> Do this after installing the requirements


## Chrome
Chrome is needed for pyppeteer which is required to auto upload to the site. 
 
 ### Linux
> - These instructions are if you want to download a more up to date version/your own version of chrome. A chrome binary will be provided for Linux
> 
> - Easiest Method is to just follow your linux providers instructions. However this usually requires sudo access.
> - If you don't have sudo you could try to get this version:https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/843831/
> - Download it and move it to ./empuploader/bin/Chrome-Linux
> - Then Extract it 

### Windows

> - Download and install a non portable version of chrome
> - it should be in your x86 program files folder. This is the default install directory on 64bit Windows
## Gifsicle

### Linux
sudo apt-get install gifsicle

### Windows
See: https://eternallybored.org/misc/gifsicle/


## Note:
* on Linux you may need to chmod + x -R ./bin/ to give permession to the binaries in that folder

## Step 4: Cookies

There are numberous extensions that can export cookies in a json format. Some Recommendations are below, but it is not required to use those specific ones


You should be exporting the data as a json
Their should be "brackets,colons,curlybrackets" as part of the text
Copy the provided text into a file, and pass that file into the program with the --cookie arg or config file.


### Recomendations

#### Chrome or Opera,Chromium Browsers 

* editthiscookie:https://www.editthiscookie.com/blog/
* Exporting Cookies: Follow the instructions here -> https://www.editthiscookie.com/blog/2014/03/import-export-cookies/


#### Firefox 

* cookie-quick-manager:https://addons.mozilla.org/en-CA/firefox/addon/cookie-quick-manager/?utm_source=addons.mozilla.org&utm_medium=referral&utm_content=search
* Exporting Cookies: This is button to look for ->  https://addons.mozilla.org/user-media/previews/thumbs/211/211229.jpg?modified=1622132880

1. You'll want to click the icon on the extension bar
2. Click Search for Cookies
3. Look for the folder Icon 
4. Click Copy all



# ARGs

> --torrents 
>  - Path where torrentfile will  save
> 
> --data
> - This is the path where json files are stored
> 
> --trackerurl
> - url to save upload with
> - Your personal url is on the upload page
> 
> --media
> - Directory to retrieve files/folders 
> 
> --screens
> - Set a folder to save thumbs in; default is random tempdir
> 
> --batch
> - If set to false any folder will be consider one entry to be uploaded
> - true then every element in directory will be A seperate upload 
> --input
> - Change the path of the json that is generated 
> 
> --cover
> - Provide the full path to the cover image
> - if selected then this image we replace any gif that would have been created
> > 
> > --image
> - add static images to your upload
> 
> --template
> - template is read, and information on text json is updated
> 
> --cookie
> - with content in the json format
> 
> 
> --config
> - use config to import arguments into program
> 
>--font
> - change the font file utilize by mtn to generate thumbs





