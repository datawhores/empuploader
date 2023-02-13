This script automates the process of uploading

https://github.com/excludedBittern8/empuploader/wiki/Uploading-Torrents


# Requirements

> - Python 3.6 or higher


# Install
## Part 1: Installing the Software

### Linux
- git clone https://github.com/excludedBittern8/empuploader
- cd empuploader
- python3 -m pip install --user virtualenv
- python3 -m venv env
- source env/bin/activate
- which python -> should be the virtualenv
- pip3 install -r requirements.txt
- pip install imageio[ffmpeg]
- on Linux you may need to chmod + x -R ./bin/ to give permission to the binaries in that folder
- deactivate -> Do this after installing the requirements
#### Optional 
Chrome can be installed through this link https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/843831/
it can also be installed automatically

### Windows
- git clone https://github.com/excludedBittern8/empuploader
- cd empuploader
- git clone ​
- py -3 -m pip install --user virtualenv
- py -3 -m venv env
- .\env\Scripts\activate
- which python -> should be the virtualenv
- py -m pip install -r requirements.txt
- pip install imageio[ffmpeg]
- deactivate -> Do this after installing the requirements
### Chrome
You should install chrome for windows through the chrome web site



## Part 2: Cookies

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




# Running the program

## Setup
- cd /empuploader 
- source env/bin/activate -> on linux or .\env\Scripts\activate -> on windows

## Modes
There are 4 Modes you can run 
- prepare mode: scans a folder/ file and prepares the data required for upload. Manditory step
- edit mode: Edit details of an upload
- preview mode: Preview an upload before upload
- upload mode: upload a torrent

## command/args
Please read the wiki for example commands: https://github.com/excludedBittern8/empuploader/wiki

Read the next section for general guidelines

- python3 empuplpader {global-args} [mode] {mode-args}

### global args
Args that appear before the mode, and they apply changes in multiple modes


`
--config  [optional]
 ```
   path to config file
   Note: Config file negates any required args
   Note: If a arg is passed with config arg set, the arg is given higher priority then        any config args
 ```


--cookie [required]
 ```
cookie File for preview and upload mode
 ```


--template [optional]
 ```
Template file for creating desc string
 ```


 --output [optional]
  ```
   prepare mode: Path to dir or a yml/yaml terminated path to store text file
   other modes: full path or dir where a previously created yml or yaml is stored
 ```
 
 --output [optional]
  ```
   prepare mode: Path to dir or a yml/yaml terminated path to store text file
   other modes: full path or dir where a previously created yml or yaml is stored
 ```

### prepare mode args
These are for prepare mode only
--media [required]
```
Directory to retrive media files
```

--torrent[required]
```
Directory to store torrent files
```

--picdic[optional]
```
 Path to store output mediafiles Stored in
```
 
--tracker[required]
```
 Your tracker announce url
```

--cover[optional]
```
 set a preset image to use for cover image
```

--images[optional]
```
 scan a directory for images
```

--exclude[optional]
```
   file patterns for dottorrent to exclude
   Can be passed multiple times 
   regex match
```                       
--manual
```
 Manually select which files to include
  ```
## edit mode args
```
Edit Mode only has global args
```

## preview mode args
```
Preview Mode only has global args
```
## upload mode args
```
Preview Mode only has global args
```







