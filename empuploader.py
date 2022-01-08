#! /usr/bin/env python3
from bs4 import BeautifulSoup
import os
from shutil import which
import sys
from threading import Thread
from pprint import pprint
from prompt_toolkit import prompt as input
import empupload.general as general


"""
Main Driver for Program

:param: None
:returns: None
"""

if __name__ == '__main__':
    #setup path
  workingdir=os.path.dirname(os.path.abspath(__file__))
  binfolder=os.path.join(workingdir,"bin")
  binlist=[]
  t=os.listdir(binfolder)
  for path in t:
      full=os.path.join(binfolder,path)
      if os.path.isdir(full) and full not in os.environ["PATH"]:
          binlist.append(full)
  os.environ["PATH"] += os.pathsep + os.pathsep.join(binlist)
  args=general.setup_parser()
  general.create_config(args)
  if sys.platform=="linux":
    general.create_binaries_linux(args)
  else:
    general.create_binaries_windows(args)
  if general.valid_dir(args)==False:
    quit()
  general.preparer(args)
   

 