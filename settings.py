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
chromeURL="https://github.com/macchrome/linchrome/releases/download/v108.5359.98-M108.0.5359.98-r1016-portable-ungoogled-Lin64/ungoogled-chromium_108.0.5359.98_1.vaapi_linux.tar.xz"




#binaries
chrome_Linux=which("google-chrome-stable") or which("google-chrome-beta") or which("google-chrome-dev") or which("chrome") or os.path.join(workingdir,"bin/chrome_Linux/chrome")
chrome_Windows=which("chrome.exe") or which("google-chrome.exe") or \
os.path.join(os.environ.get("ProgramFiles",""),"Google\Chrome\Application\chrome.exe")
ffmpeg=os.path.join(workingdir,"bin/ffmpeg")
gifsicle=os.path.join(workingdir,"bin/gifsicle")
mtn_Linux=os.path.join(workingdir,"bin/mtn_Linux/mtn")
mtn_Windows=os.path.join(workingdir,"bin/mtn_Windows/mtn.exe")
#These are to help reduce post size to meet size limits
postthumbsSize=100
maxpostThumbs=20

#other
font=os.path.join(workingdir,"data/OpenSans-Regular.ttf")

