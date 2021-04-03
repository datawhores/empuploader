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


--torrent 
> - Path where torrentfile will  save

--data
> - This is the path where json files are stored

--trackerurl
> - url to save upload with
> - Your personal url is on the upload page

--media
> - Directory to retrieve files/folders 

--screens
> - Set a folder to save thumbs in; default is random tempdir

--batch
> - If set to false any folder will be consider one entry to be uploaded

--input
> - Change the path of the json that is generated 

--cover
> - Provide the full path to the cover image
> - if selected then this image we replace any gif that would have been created

--template
> -use optional template system, read below for full instruction

--username
> - your emp username

--passsword
> - your emp password
> 
## Using Template
> - To use the template system you will need to first download the template you want and save it to a txt file
> - This can be found on the upload page depending on your class
> 
### What are Placeholders
> - Templates will usually generally provide places for things like your description, screens, etc
> - This information is frequently changing depending on the upload
> - placeholders allow you to dynamically alter your upload description while allowing for the use of templates
### Adding place holders
> - Before the template can be used succefully used you will need to put in the placeholders {cover} {title} {thumbs} {tags} {desc} are the main ones
> - See below in other sections for more advanced ones
> - Note: placeholders include the brackets on the left and right side. They are also case sensitive all lower case
> - Each of these can be put in the template as many or as little times as you want. 
> - So for example if a template has a spot where maybe it says *** screens *** you could replace it so it says {images}
> - When the program uploads your torrent it will use your template to generate the description
> - I have provided an example template at example_template.txt


### Video/Audio placeholders
 For advance users I have provided placeholders for mediainfo

 ##### Example Video Info
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
> - You'll have to look at the json in the video: and audio: sections to get a better understanding of what values you have avaluable
> - To utilize for example duration  as a placeholder I would have to put this into the template {video.duration}
> - When the torrent is posted that would be replaced by 10 min 14 via the template
> - Another example would be {video.display_aspect_ratio} 
> - When the torrent is posted that would be replaced by 16:9 via the template

### Images placeholders
 For advance users you can use static images as placeholders
 
> - You will need to provide the --image argument via config or commandline 
> - Each image must have a unique name within the imagedirectory
> - Note: Unique name excludes the path so /img/imgs2/myimage and /img/imgs/myimage is not allowed. Both of those must
> have a unique name so /img/imgs/myimage2.jpg  /img/imgs2/myimage2.jpg is allowed
> - I would recommend using short and informative names
> - Any nested of directories is allowed within the imagedirectory
> - to access an image utilize {image.[name of image]} as the placeholder

##### Example
>- I have an image called myimage2.jpg 
>- to use this image I would have the placeholder {images.myimage2.jpg}
# Upload

Prompted with the -upload flag
Run after creating a json with prepare



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
> - If you not using templates then this mode is not needed
> 

## Required Args
--template
> - template is read, and information on the json is updated

