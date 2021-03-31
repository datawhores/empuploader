If you already had a older verison of the tool. Please reread this as the usage has changed dramatically
This tool will prepare and upload torrents to currently this tool.

# Requirements
- Python 3.6 or higher
- sudo access
- chrome(read install instruction)
- gifsicle(read install instruction)



Note:
A script may be provided to allow none sudo users to gain some upload access. It would work from the browser directly and would be used along side this python script. The same issue may also apply to those who have 2f on

# Install

## Virtual Env

Installing virtualenv
On macOS and Linux:

python3 -m pip install --user virtualenv

On Windows:

py -m pip install --user virtualenv

Creating the virtualenv
On Linux:

python3 -m venv venv

On Windows:

python3 -m venv venv

alternatively

py -m venv venv

Add required modules
On Linux:

./venv/bin/pip3 install -r requirements.txt

On Windows:

venv\Scripts\pip3.exe install -r requirements.txt

Running python from venv
On Linux

/venv/bin/python3

on Windows

venv\Scripts\python

## gifsicle
- on linux you will need to install sudo apt-get install gifsicle
- on Windows they provide binaries at https://eternallybored.org/misc/gifsicle/
- the binary should be in your path and callable via gifsicle or gifsicle.exe depending on your os

## ffmpeg
- The required binaries are in the ffmpeg-win for windows user
- For linux it is ffmpeg-unix
- Note the binaries can not be used from these directories instead they must be save to your path.
- For linux users with sudo please read about how to install ffmpeg and ffprope
- For Windows user if you need help please come to the site, or ask on github. The binaries must be in your windows path
- Windows Updated Builds:https://www.gyan.dev/ffmpeg/builds/
- Linux Updated Builds:https://johnvansickle.com/ffmpeg/

## vcsi
- if you have trouble installing please checkout-> ttps://github.com/amietn/vcsi
- You will need to have ffmpeg and ffprope in your path

## need Chrome?
 
 **Linux

-Easiest Method is to just follow your linux provideres instructions. However this usually requires sudo access.
- If you don't have sudo you could try to get this version:https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/843831/
- Download it and move it into the Linux Folder, within the bin folder, Within the empuploader folder or ../empuploader/bin/Linux
- Extract it

** Windows
- Download and install a non portable version of chrome

# Intro
Their are two modes in this program you must pick one and only 1 of the following commandline flags/options

-prepare 
- will set prepare mode. This will prepare all the information needed for uploaded. It will create a json file. The loctation of the json file will be in predetermined directory. Alternatly you can pick a specific path

-upload 
- will set upload mode. This will work with python to automatically sign you in, and fill the upload form. It will be just like you were filling out the form yourself

# Config File
Instead of using the command like options like empuploader.py --option1 --option2 ......
- The config file provides an easy way to load multiple arguments with one argument
- empuploader --config /path/to/config
- Note: you can always overwrite a config option with a command line argument
- Also Note: If you don't want to set an option in config just include the name, and nothing else
- To set a value put an = sign then the value you would like


# Prepare

iniatiated with the -prepare flag


## Required Args


--torrent 
- path where torrentfile will  save

--data
- path where json will  save

--trackerurl
- url to save upload with

--media
- directory to retrieve files/folders from

## Optional Args

--screens
- by default screens will be save to a random directory, then moved only if it is required. 
- You can use this option to pick your own directory

--batch
- When set to false only 1 file will be processed, afterwards program will quit

--input
- Change the Name of the json that is generated 

--template
-use optional template system, read below for full instructions
-This would be the path to the template you want to use

--dottorent
- No need to set this, but if you have a version of this binary in a different path, you can use this to change the path within the program. 
- Used to create torrents with other arguments selected

--fd
- No need to set this, but if you have a version of this binary in a different path, you can use this to change the path within the program. 
- Used to search for files and directories from commandline

## Entering Data into jsons
- When you run the program in prepare mode you will be provide opportunity to fill some of the option with your own data
- Note the provided will allow you to always move backwards and forwards, so editing a mistake will be easy

### Tags
- Tags should be seperated by spaces

### Title
- Comes with autofill to activate press tab, and a name based on what your uploading will be provided. - - Note you can enter your value or edit the one provided above

### Description
- Allows for multiline inputs unlike the previous option
- To "enter" or submit you must press esc+enter
- Note \n represents a newline. This is generated automatically. But if you want to edit the json manually, make sure to put these everytime you want a line break

## Using Template

- To use the template system you will need to first download the template you want and save it to a txt file
- Before the template can be used succefully used you will need to put in the placeholders {cover} {title} {images} {tags} {desc}.
- Note: placeholders include the brackets on the left and right side. Case insensitive
- Each of these can be put in the template as many or as little times as you want. 
- So for example if a template has a spot where maybe it says *** screens *** you could replace it so it says {images}
- When the program creates your post descreption. It will generate the info, and replace any placeholder in the template you added with the info it created



# Upload

iniatiated with the -upload flag

## Required Args
-data
- This is the path where json files are saved by default
- Will combine the -data directory path, along with the name of what your trying to upload to find the json file. This should generate the correct path to autoload the correct json file
- Note if you use -input instead then this option is not required

--media
- directory to retrieve files/folders from

-username
- your emp username
- used to login
passsword
- your emp password
- used to login
- Note: if you have 2f then that is correctly not supported 
## Notes
- Note: you must have already ran -prepare to genearate a json
- Second Note: If you don't select a username and password, or automatic upload doesn't work. Info will be saved to a self destructing paste on  uguu.se

## Optional Args


-input
- use this to change the path of where the input json comes from
- Only needed if you change the name of the file using input while --prepare 

--batch
- When set to false only 1 file will be uploaded, afterwards program will quit
