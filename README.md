This script automates the process of uploading

https://github.com/excludedBittern8/empuploader/wiki/Uploading-Torrents


# Requirements

> - Python 3.6 or higher


# Install
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
#### Chrome
Install Chrome with playwright

- cd empuploader
- source env/bin/activate
- pip install playwright

##### Next step requires sudo
- playwright install chromium

Don't have sudo?

Don't worry the script will auto download a portable version of chromium for you

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
- playwright install chromium
- deactivate -> Do this after installing the requirements
### Chrome
You should install chrome for windows through the chrome web site


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
Please read the wiki for example commands and how to run: https://github.com/excludedBittern8/empuploader/wiki

Please read the following for arguments to pass
https://github.com/excludedBittern8/empuploader/wiki/commands-and-args


