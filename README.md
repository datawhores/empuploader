Ready to Upload?
Then read the Wiki
https://github.com/excludedBittern8/empuploader/wiki/Uploading-Torrents

Otherwise Install Instruction and an overview of the availible commands are below


# Requirements

> - Python 3.6 or higher
> - chrome


# Install
## Step 1: Repo
> - git clone https://github.com/excludedBittern8/empuploader
> - cd empuploader

## Step 2: Virtual Env
* This will allow you to install packages for this project only. Without effecting the global install of python
* This is the recommended method, as it protects from conflicting packages. It also will work without sudo on Linux

### Linux
> #### create virtual venv
> 
> - python3 -m pip install --user virtualenv
> - python3 -m venv venv
> 
> 
> 
> #### Add required modules
> ./venv/bin/pip3 install -r requirements.txt
> #### Running 
> /venv/bin/python3

### Windows
#### create virtual venv

> py -m pip install --user virtualenv
> 
> python3 -m venv venv
> 
> alternatively
> 
> py -m venv venv
> 
> 
> 
> #### Add required modules
> 
> venv\Scripts\pip3.exe install -r requirements.txt
> 
> #### Running
> 
> venv\Scripts\python


## Step 3: Chrome
Chrome is needed for pyppeteer which is required to auto upload to the site. 
 
 ### Linux

> - Easiest Method is to just follow your linux providers instructions. However this usually requires sudo access.
> - If you don't have sudo you could try to get this version:https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/843831/
> - Download it and move it to ./empuploader/bin/Chrome-Linux
> - Then Extract it 

### Windows

> - Download and install a non portable version of chrome
> - it should be in your x86 program files folder. This is the default install directory on 64bit Windows



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
> 
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
> --username
> - your emp username
> 
> --passsword
> - your emp password

--config
> - use config to import arguments into program
--font
> - change the font file utilize by mtn to generate thumbs





