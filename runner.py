#! /usr/bin/env python3
import os
from shutil import which
import general.arguments as arguments
import general.console as console
import general.selection as selection
import general.paths as paths
import empupload.modes as modes

args=arguments.getargs()
"""
Performs Action on single directory/File based on User input

:param args: user Commandline/Config arguments
:param path: path chosen by user
:returns: None
"""
# def processor(index,path,args):
#     elif index==1:
#         print("Upload Mode\n")
#         createImages(get_workdir())
#         emp.pre_upload_emp(args,path)
#     elif index==2:
#         print("Update Template Mode\n")
#         yamlpath=emp.start_yaml(basename,args)
#         emp.update_template(args,yamlpath)
#     elif index==3:
#         print("Torrent Creator Mode\n")
#         torrentpath=os.path.join(args.torrents,f"{basename}.torrent")
#         emp.create_torrent(path,torrentpath,args)



          


"""
Prompts User to Select a specific file/Directory
Prepares Processor

:param args: user Commandline/Config arguments
:param choices: List of Possible Paths
:returns: None
"""
def start():
    while True:
        console.console.print(f"{args.subcommand.capitalize()} Mode",style="green")
        if args.subcommand=="prepare":
                path=selection.singleoptions(msg="Which path Do you want to prepare",choices=paths.get_choices())
                yamlpath=paths.generate_yaml(path)
                modes.process_yaml(path,yamlpath)
        elif args.subcommand=="edit":
            yamlpath=args.output
            if not yamlpath.endswith(".yml") and not yamlpath.endswith(".yaml"):
                yamlpath=selection.singleoptions("Which yml do you want to edit",paths.retrive_yaml(yamlpath))
            modes.update_template(yamlpath)
        elif args.subcommand=="preview":
            print(modes.generatepreview())

        if selection.singleoptions(msg=f"Run {args.subcommand.capitalize()} mode again?",choices=["Yes","No"])=="No":
            break
  
    
        




"""
Set Binaries on Linux

:param args: user Commandline/Config arguments

:returns: sets args for all required binaries
"""

# `def create_binaries_linux(args):
#     workingdir=get_workdir()
#     if args.font==None:
#         args.font=os.path.join(workingdir,"bin","mtn","OpenSans-Regular.ttf")
#     if which('ffprobe')!=None and len(which('ffprobe'))>0:
#         args.ffprobe=which('ffprobe')
#     else:
#         ffprobe=os.path.join(workingdir,"bin","ffmpeg-unix","ffprobe")
#         args.ffprobe=ffprobe
#     if which('ffmpeg')!=None and len(which('ffmpeg'))>0:
#         args.ffmpeg=which('ffmpeg')
#     else:
#         ffmpeg=os.path.join(workingdir,"bin","ffmpeg-unix","ffmpeg")
#         args.ffmpeg=ffmpeg
#     if which('mtn')!=None and len(which('mtn'))>0:
#         args.mtn=which('mtn')
#     else:
#         mtn=os.path.join(workingdir,"bin","mtn","mtn")
#         args.mtn.exe=mtn
#     if which('fd')!=None and len(which('fd'))>0:
#         args.fd=which('fd')
#     else:
#         fd=os.path.join(workingdir,"bin","fd")
#         args.fd=fd

#     if which("dottorrent")!=None and len(which('dottorrent'))>0:
#         args.dottorrent=which('dottorrent')
#     else:
#         dottorrent=os.path.join(workingdir,"bin","dottorrent")
#         args.dottorrent=dottorrent`
"""
Set Binaries on Windows

:param args: user Commandline/Config arguments

:returns: sets args for all required binaries
"""


def create_binaries_windows(args):
    workingdir=get_workdir()
    if which('ffprobe.exe')!=None and len(which('ffprobe.exe'))>0:
        args.ffprobe=which('ffprobe.exe')
    else:
        ffprobe=os.path.join(workingdir,"bin","ffmpeg-win","ffprobe.exe")
        args.ffprobe=ffprobe
    if which('ffmpeg.exe')!=None and len(which('ffmpeg.exe'))>0:
        args.ffmpeg=which('ffmpeg.exe')
    else:
        ffmpeg=os.path.join(workingdir,"bin","ffmpeg-win","ffmpeg.exe")
        args.ffmpeg=ffmpeg
    if which('mtn.exe')!=None and len(which('mtn.exe'))>0:
        args.mtn=which('mtn.exe')
    else:
        mtn=os.path.join(workingdir,"bin","mtn","mtn.exe")
        args.mtn.exe=mtn
    if which('fd.exe')!=None and len(which('fd.exe'))>0:
        args.fd=which('fd.exe')
    else:
        fd=os.path.join(workingdir,"bin","fd.exe")
        args.fd=fd
    if which("dottorrent.exe")!=None and len(which('dottorrent'))>0:
        args.dottorrent=which('dottorrent')
    else:
        dottorrent=os.path.join(workingdir,"bin","dottorrent.exe")
        args.dottorrent=dottorrent
    
"""
Set PATH 

:param binfolder: bin directory of program

:returns: None
"""


def setPath(binfolder):
    t=os.listdir(binfolder)
    binlist=[]
    for path in t:
        full=os.path.join(binfolder,path)
        if os.path.isdir(full) and full not in os.environ["PATH"]:
            binlist.append(full)
    os.environ["PATH"] += os.pathsep + os.pathsep.join(binlist)

