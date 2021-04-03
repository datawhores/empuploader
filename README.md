If you already had a older verison of the tool. Please reread this as the usage has changed dramatically
This tool will prepare and upload torrents to Empornium, all through the commandline.

You can use provide your own template to create informative/eye-catching post

# Requirements

> - Python 3.6 or higher
> - sudo access
> - chrome(read install instruction)
> - gifsicle(read install instruction)




# Install
> - git clone https://github.com/excludedBittern8/empuploader
> - cd empuploader


## Virtual Env

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


## PATH

> - You will need to add a few programs to a your path to use this script. This allows programs to be called with just their name, and not the full path
> - Windows: https://www.computerhope.com/issues/ch000549.htm
> - Linux: https://stackabuse.com/how-to-permanently-set-path-in-linux/ (most people should use bash_profile or bash.rc)
> - On Linux you can use a folder like usr/local/bin. However if you don't have root. It might be better to try to add your own folder
> - On Windows: I would try to add my own folder to path. As the paths already in your PATH may be tied to other programs, and may change.  A restart may be needed to active the changes. 


## gifsicle 

> - on linux you will need to install sudo apt-get install gifsicle; this will put the binary in your path
> - on Windows the creators provide binaries at https://eternallybored.org/misc/gifsicle/
> - the binary should be in your path and callable via gifsicle or gifsicle.exe depending on your os


## Need Chrome?
Chrome is needed for pyppeteer which is required to auto upload to the site. 
 
 ### Linux


> - Easiest Method is to just follow your linux providers instructions. However this usually requires sudo access.
> - If you don't have sudo you could try to get this version:https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/843831/
> - Download it and move it into the Linux Folder, within the bin folder, Within the empuploader folder or ../empuploader/bin/Linux 
> - Then Extract it 


### Windows

> - Download and install a non portable version of chrome
> - I am assuming most people are not on 32 bits anymore, so it should be in your x86 program files folder. This is the default install directory

## Optional binaries

> - https://gitlab.com/movie_thumbnailer/mtn/-/releases
> - https://github.com/sharkdp/fd/releases
> - https://github.com/kz26/dottorrent-cli
> - These Binaries are all provided, but if you want to upgrade to a newer version. Links have been provided

# ARGs

> --torrent 
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
> 
> --template
> - template is read, and information on text json is updated
> 
> --username
> - your emp username
> 
> --passsword
> - your emp password







