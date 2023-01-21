import tempfile
####
# More Advance Settings 
#
####
import os
workingdir=os.path.dirname(os.path.abspath(__file__))
binfolder=os.path.join(workingdir,"bin")
#https://github.com/macchrome/linchrome/releases
chromeURL="https://github.com/macchrome/linchrome/releases/download/v108.5359.98-M108.0.5359.98-r1016-portable-ungoogled-Lin64/ungoogled-chromium_108.0.5359.98_1.vaapi_linux.tar.xz"
tmpfile=tempfile.gettempdir()
font=os.path.join(workingdir,"bin","mtn","OpenSans-Regular.ttf")
mtn=os.path.join(workingdir,"bin","mtn","mtn")