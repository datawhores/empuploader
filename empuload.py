I made a tool meant to be a 1-click solution to prepare everything needed for upload
Command: empuploader.py prepare /dir/
This tool will process your folder/file
[*]by creating a gif
[*]Move images to uploading folder or zip if needed
[*] Creating a description with images 
[*] making a torrent file
[*] uploading a max of 100 images
[*] outputs a paste url that is destroyed in 24 hours, also saves it to a txt file
I don't have access to templates yet, but hopefully it will be easy to implement with that. 

The process to run it is to just create txt files with minimum needed for uploads
[*]title
[*]tags
[*]description
  
config:by default it should be in the home config directory put can be overwritten with
[*]config=/path


First the config file is checked. These parameters will overwrite any config file option
[*]--screens=<screens> --torrents=<torrents> --txtlocation=<txtlocation> --trackerurl=<trackerurl> --config=<configpath>
[*]All these parameters are required to be in the config file or to be entered in the command

Final Output:.uguu.se where information can be quickly pasted into the upload form

Dependencies:
python3
fd
vcsi
pygifsicle
BeautifulSoup
ffprobe
dottorrent
imageio

It should run on
-mixed uploads with video and images
- uploads with images only
- uploads with videos only





