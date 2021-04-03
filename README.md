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


## ffmpeg
> - The required binaries are in the ffmpeg-win for windows user
> - For linux it is ffmpeg-unix and Windows is ffmpeg-win
> - Note the binaries are provided for convience. They must be save to your PATH.
> - Linux users with sudo please read about how to install ffmpeg and ffprope. It may change depending on your specific OS
> - Linux Updated Builds: https://johnvansickle.com/ffmpeg/
> - Windows user if you need help please come to the site, or ask on github. The binaries must be in your windows PATH.
> - Windows Updated Builds: https://www.gyan.dev/ffmpeg/builds/



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

## Other binaries

> - https://gitlab.com/movie_thumbnailer/mtn/-/releases
> - https://github.com/sharkdp/fd/releases
> - https://github.com/kz26/dottorrent-cli
> - These Binaries are all provided, but if you want to upgrade to a newer version. Links have been provided
> - It is recommended to put these in your path


# Intro
Their are three modes in this program you must pick one and only 1 of the following commandline flags/options during a run

## -prepare 
> - will set prepare mode. This will prepare all the information needed for uploaded. It will create a json file. The loctation of the json file will be in user-determined directory.  Alternatively you can pick a specific path

## -upload 
> - will set upload mode. This will work with python to automatically sign you in, and fill the upload form. It will be just like you were filling out the form yourself
> 
## -update
> - will set update template mode. 
> - This will take the current json and update the template info

# Config File
Instead of using the command like options like empuploader.py --option1 --option2 ......

> - The config file provides an easy way to load multiple arguments with one argument
> - empuploader --config /path/to/config
> - Note: you can always overwrite a config option with a command line argument
> - Also Note: If you don't want to set an option in config just include the name, and nothing else
> - To set a value put an = sign then the value you would like
> - An Example Config is provided in the repo as empupload.conf


# Prepare

prompted by the -prepare flag


## Required Args


--torrent 
> - Path where torrentfile will  save

--data
> - Path where json will be save
> - Note:overridden by --input option if that option is set



--trackerurl
> - url to save upload with
> - Your personal url is on the upload page

--media
> - Directory to retrieve files/folders 
> - You will be able to pick one of these to prepare


## Optional Args

--screens
> - by default screens will be save to a random directory tempdir, then moved only if it is required. 
> - You can use this option to pick your own directory

--batch
> - When set to false only 1 file will be processed, afterwards program will quit
> - By default the program will list every entry in a directory as processing option, this prevents that behavior

--input
> - Change the Name of the json that is generated 

--cover
> - Provide the full path to the cover image
> - if selected then this image we replace any gif that would have been created

--template
> -use optional template system, read below for full instructions
> -This would be the path to the template you want to use


## Entering Data into jsons
> - When you run the program in prepare mode you will be provide opportunity to fill some of the option with your own data
> - Note the provided will allow you to always move backwards and forwards, so editing a mistake is easy
> - Pressing Tab on Some options will provide auto suggestions
> 

### Tags
> - Tags should be seperated by spaces

### Title
> - Comes with autofill to activate press tab, and a name based on what your uploading will be provided 
> - Note you can enter your own value or edit the one provided above


### Category
> - Comes with autofill to activate press tab, and a list of categories will appear
> - Alternativey suggestions will appear as you type 
> - You can use the keepboard to select one or keep typing

### Description
> - Allows for multiline inputs unlike the previous option
> - To "enter" or submit you must press esc+enter
> - Note \n represents a newline. This is generated automatically. But if you want to edit the json manually, make sure to put these everytime you want a line break

## Using Template
> - To use the template system you will need to first download the template you want and save it to a txt file
> - This can be found on the upload page depending on your class
> - Before the template can be used succefully used you will need to put in the placeholders {cover} {title} {images} {tags} {desc}.
> - Note: placeholders include the brackets on the left and right side. They are also case sensitive all lower case
> - Each of these can be put in the template as many or as little times as you want. 
> - So for example if a template has a spot where maybe it says *** screens *** you could replace it so it says {images}
> - When the program uploads your torrent it will use your template to generate the description
> - I have provided an example template at example_template.txt


### Video/Audio placeholders
 For advance users I have provided placeholders for mediainfo

 ** Example Video Info**
``
```
'video': {'bit_depth': '8 '
                        'bits',
           'bit_rate': '12.0 '
                       'Mb/s',
           'bit_rate_mode': 'Variable',
           'bits__pixel_frame': '0.434',
           'chroma_subsampling': '4:2:0',
           'codec_id': 'avc1',
           'codec_id_info': 'Advanced '
                            'Video '
                            'Coding',
           'color_primaries': 'BT.709',
           'color_range': 'Limited',
           'color_space': 'YUV',
           'display_aspect_ratio': '16:9',
           'duration': '10 '
                       'min '
                       '14 '
                       's',}
```

> - Note the example above is not an extensive list of all the possible values
> - You'll have to look at the json to get a better understanding of what values you have avaluable
> - To utilize for example duration as a placeholder I would have to put this into the template {video.duration}
> - When the torrent is posted that would be replaced by 10 min 14 via the template
> - Another example would be {video.display_aspect_ratio} 
> - When the torrent is posted that would be replaced by 16:9 via the template

# Upload

Prompted with the -upload flag
Run after creating a json with prepare

## Required Args
--data
> - This is the path where json files are saved by default
> - Program will combine the -data directory, along with the name of what your trying to upload. This should generate the correct path to autoload the correct json file
> - Note: overridden by --input option if that option is set

--media
> - directory to retrieve files/folders from
> - You will be able to pick one of these to upload

--username
> - your emp username
> - used to login

--passsword
> - your emp password
> - used to login
> - Note: if you have 2f then that is correctly not supported. 
> - An API is upcoming so that will provide better authentication for users

## Optional Args
> --input
> - use this to change the path of where the input json comes from
> - Only needed if you change the name of the file using input while --prepare 

--batch
> - When set to false only 1 file will be uploaded, afterwards program will quit
> - By default the program will list every entry in a directory as upload option, this prevents that behavior

## Upload Not Appearing
> - Program Doesn't error out but upload still doesn't appear on profile?
> - Check your program directory, and look at the file call final.jpg
> - This file will show a picture of the result after click the "submit" button
> - Utilize this to see if you made a mistake for example not including 8 tags, or if your template doesn't have any images, etc

# Update
> - Updating the json requires some understanding on how python strings work. 
> - Json can not intrepret regular line breaks, so it uses the python syntax of \n for line breaks
