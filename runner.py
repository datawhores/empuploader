#! /usr/bin/env python3
import pathlib
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
                input=selection.singleoptions(msg="Which path Do you want to prepare?",choices=paths.get_choices())
                ymlpath=paths.generate_yaml(input)
                modes.process_yml(input,ymlpath)
        
        else:
            ymlpath=args.output
            ymlSelection=paths.retrive_yaml(ymlpath)
            if pathlib.Path(ymlpath).is_file():
                None
            elif pathlib.Path(ymlpath).is_dir() and len(ymlSelection)>0:
                 ymlpath=selection.singleoptions(f"Which yml do you want to use for {args.subcommand}ing?",ymlSelection)
            else:
                console.console.print("ymlpath does not exist\nor non configuration files present")
                quit()

            if args.subcommand=="edit":
                modes.update_yml(ymlpath)
            elif args.subcommand=="preview":
                modes.generatepreview(ymlpath)
            elif args.subcommand=="upload":
                modes.upload(ymlpath)
            if selection.singleoptions(msg=f"Run {args.subcommand.capitalize()} mode again?",choices=["Yes","No"])=="No":
                break
    





