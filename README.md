Dependencies:
    python3
    fd
    vcsi
    pygifsicle
    BeautifulSoup
    ffprobe
    dottorrent
    imageio

This is a a tool to quickly prepare folders for upload.

It won't work for every type of upload, but it will do well if your looking to upload lots of torrents with gif covers.

How to use
Clone the repository or download the python file.
Move or copy the config example to your /home/user/.config/ or /root/.config/ make sure to replace the values 
-Currently their aren't really any options in this script everything is required and the assumtion is that you'll want everything that it provides. Saying that the config only servers to change where things end up on your system
- if a value is not in the config the it can and most be overwritten in the command with the syntax option="your choice"
- values can be over written with option="your choice" even if they are in the config
- Create a txt file with the same name as your upload basename, which is the name of the file or folder itself. No extension. Exclude other folders for example /home/sexy would be sexy /home/sexy.mp4 would also be sexy for the basename


txt file:
Used to create descriptions and gather details about your upload
First line = Title
Second line = Tags
Otherlines= Description

Note: This program will send the output to 
uguu.se  which self destructs in 24 hours


optional:https://github.com/billziss-gh/sshfs-win
Basically allows for remote ssh to be mounted as a regular drive, so you don't have to rclone mount or move the torrent directly

