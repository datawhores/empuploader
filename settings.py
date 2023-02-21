import tempfile
import os
from shutil import which
"""
Advanced Settings
"""
#folders
workingdir=os.path.dirname(os.path.abspath(__file__))
binfolder=os.path.join(workingdir,"bin")
tmpdir=tempfile.gettempdir()
#urls
empURl="https://www.empornium.is"


#binaries
ffmpeg=os.path.join(workingdir,"bin/ffmpeg")
gifsicle=os.path.join(workingdir,"bin/gifsicle")
mtn=os.path.join(workingdir,"bin/mtn")
#These are to help reduce post size to meet size limits
postImageSize=300
maxNumPostImages=20

#other
font=os.path.join(workingdir,"data/OpenSans-Regular.ttf")
gifLength=5
#value 1-100 on where to start gif
gifStart=75



