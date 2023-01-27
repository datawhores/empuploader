from InquirerPy import inquirer
import InquirerPy
import general.console as console
"""
Provides a menu limited by one choice
:params msg: msg to print on menu
:params choices: list of choices to pick from
:params default: choice to highlight on init
:returns any: choice selected
"""
def singleoptions(msg,choices,default=None,mandatory =True,validate=None):
    if not validate:
        validate=lambda selection: len(selection) >= 1
    return inquirer.select(
        message=msg,
        choices=choices,
        default=default,
        validate=validate,
        mandatory =mandatory 
    ).execute()

"""
Provides a menu that allows multiple choices
:params msg: msg to print on menu
:params choices: list of choices to pick from
:params default: choice to highlight on init
:returns any: choice selected
"""
def multioptions(msg,choices,mandatory =True,default=None,instruction=None,validate=None,transformer=None):
    if not instruction:
        instruction=\
            """
            Press Space to toggle choic
            Press Enter to submit
            CTRL-R toggles all
            """
    if not validate:
        validate=lambda selection: len(selection) >= 1
    return inquirer.checkbox(
        message=msg,
        choices=choices,
        default=default,
        mandatory=mandatory,
        validate=validate,
        instruction=instruction,
        transformer=transformer
    ).execute()

"""
Provides a prompt to enter a string
:params msg: msg to print on menu
:params default: choice to highlight on init
: params multiline: enable multiple lines of input
:instructions: Advanced instructions for multiline mode
:returns any: choice selected
"""
def strinput(msg,default="",multiline=False,instructions=None):
    if multiline and not instructions:
        instructions="Press Enter to Move to new line\nESC + Enter to Finish"
    return inquirer.text(message=msg,default=default,multiline=multiline,instruction=instructions).execute()
  



