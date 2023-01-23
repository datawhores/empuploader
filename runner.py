#! /usr/bin/env python3
from shutil import which
import general.arguments as arguments
import general.console as console
import general.selection as selection
import general.paths as paths
import empupload.modes as modes

args=arguments.getargs()

          
"""
Runs program in infinite loop, execution depends on arg subcommand

:returns None:
"""
def start():
    while True:
        console.console.print(f"{args.subcommand.capitalize()} Mode",style="green")
        if args.subcommand=="prepare":
                path=selection.singleoptions(msg="Which path Do you want to prepare?",choices=paths.get_choices())
                ymlpath=paths.generate_yaml(path)
                modes.process_yml(path,ymlpath)
        elif args.subcommand=="edit":
            ymlpath=args.output
            if not ymlpath.endswith(".yml") and not ymlpath.endswith(".yaml"):
                ymlpath=selection.singleoptions("Which yml do you want to edit?",paths.retrive_yaml(ymlpath))
            modes.update_yml(ymlpath)
        elif args.subcommand=="preview":
            ymlpath=args.output
            if not ymlpath.endswith(".yml") and not ymlpath.endswith(".yaml"):
                ymlpath=selection.singleoptions("Which yml do you want to use to generate a upload preview?",paths.retrive_yaml(ymlpath))
            modes.generatepreview(ymlpath)
        elif args.subcommand=="upload":
            ymlpath=args.output
            if not ymlpath.endswith(".yml") and not ymlpath.endswith(".yaml"):
                ymlpath=selection.singleoptions("Which yml do you want to use to upload?",paths.retrive_yaml(ymlpath))
            modes.upload(ymlpath)
        if selection.singleoptions(msg=f"Run {args.subcommand.capitalize()} mode again?",choices=["Yes","No"])=="No":
            break
  





