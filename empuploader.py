#! /usr/bin/env python3
import runner as runner
import empupload.puppet as puppet
import general.arguments as arguments



"""
Main Driver for Program

:param: None
:returns: None
"""

if __name__ == '__main__':
  args=arguments.getargs()
  puppet.create_chrome()
  # general.create_binaries_linux(args)
  # general.setPath(setting.binfolder)
  # else:
  #   general.create_binaries_windows(args)
  #   general.setPath(binfolder)
  # if general.valid_dir(args)==False:
  #   quit()
  runner.start()
   

 
