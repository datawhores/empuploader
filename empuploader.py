#! /usr/bin/env python3
from bs4 import BeautifulSoup
import os
from shutil import which
import sys
from threading import Thread
from pprint import pprint
from prompt_toolkit import prompt as input
import empupload.general as general
import empupload.puppet as puppet


"""
Main Driver for Program

:param: None
:returns: None
"""

if __name__ == '__main__':
    #setup path
  workingdir=os.path.dirname(os.path.abspath(__file__))
  binfolder=os.path.join(workingdir,"bin")
  args=general.setup_parser()
  general.create_config(args)
  if sys.platform=="linux":
    puppet.create_chrome(workingdir,binfolder)
    general.create_binaries_linux(args)
    general.setPath(binfolder)
  else:
    general.create_binaries_windows(args)
    general.setPath(binfolder)
  if general.valid_dir(args)==False:
    quit()
  general.preparer(args)
   

 
