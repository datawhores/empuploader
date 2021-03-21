If you already had a older verison of the tool. Please reread this as the usage has changed dramatically
This tool will prepare and upload torrents to currently this tool.

# Requirements
- Python 3.6 or higher
- sudo access
- chrome(read install instruction)
- gifsicle(read install instruction)

#install
Comaing soon


Note:
A script may be provided to allow none sudo users to gain some upload access. It would work from the browser directly and would be used along side this python script. The same issue may also apply to those who have 2f on


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


# Prepare

iniatiated with the -prepare flag


## Required Args


--torrent 
- path where torrentfile will  save

--data
- path where json will  save

--trackerurl
- url to save upload with

## Optional Args

--screens
- by default screens will be save to a random directory, then moved only if it is required. 
- You can use this option to pick your own directory

--dottorent
- No need to set this, but if you have a version of this binary in a different path, you can use this to change the path within the program. 
- Used to create torrents with other arguments selected

--fd
- No need to set this, but if you have a version of this binary in a different path, you can use this to change the path within the program. 
- Used to search for files and directories from commandline



# Upload

iniatiated with the -upload flag

## Required Args
-data
- This is the path where json files are saved by default
- Will combine the -data directory path, along with the name of what your trying to upload to find the json file. This should generate the correct path to autoload the correct json file
- Note if you use -input instead then this option is not required

## Notes
- Note: you must have already ran -prepare to genearate a json
- Second Note: If you don't select a username and password, or automatic upload doesn't work. Info will be saved to a self destructing paste on  uguu.se

# Optional Args

-username
- your emp username
- used to login
passsword
- your emp password
- used to login
- Note: if you have 2f then that is correctly not supported 

-input
- use this to change the path of where the input json comes from



Required 

It won't work for every type of upload, but it will do well if your looking to upload lots of torrents with gif covers.

--input 

This option will overwrite the --data option. Instead of saving to that predetermined directory. In
stead files will be save to the path you select here. This should be a file and not a directory



How to use
Clone the repository or download the python file.
Move or copy the config example to your /home/user/.config/ or /root/.config/ make sure to replace the values 
- Currently their aren't really any options in this script everything is required and the assumtion is that you'll want everything that it provides. Saying that the config only servers to change where things end up on your system
- if a value is not in the config the it can and most be overwritten in the command with the syntax option="your choice"
- values can be over written with option="your choice" even if they are in the config
- Create a txt file with the same name as your upload basename, which is the name of the file or folder itself. No extension. Exclude other folders for example /home/sexy would be sexy /home/sexy.mp4 would also be sexy for the basename
-

txt file:
Used to create descriptions and gather details about your upload
First line = Title
Second line = Tags
Otherlines= Description

Note: This program will send the output to 
uguu.se  which self destructs in 24 hours


optional:https://github.com/billziss-gh/sshfs-win
Basically allows for remote ssh to be mounted as a regular drive, so you don't have to rclone mount or move the torrent directly

