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
def singleoptions(msg,choices,default=None,mandatory =True,validate=None,sync=True):
    if not validate:
        validate=lambda selection: len(selection) >= 1
    result= inquirer.select(
        message=msg,
        choices=choices,
        default=default,
        validate=validate,
        mandatory =mandatory 
    )
    if sync:
        return result.execute()
    return result.execute_async()

"""
Provides a menu that allows multiple choices
:params msg: msg to print on menu
:params choices: list of choices to pick from
:params default: choice to highlight on init
:returns any: choice selected
"""
def multioptions(msg,choices,mandatory =True,default=None,instruction=None,validate=None,transformer=None,sync=True):
    if not instruction:
        instruction=\
            """
            Press Space to toggle choic
            Press Enter to submit
            CTRL-R toggles all
            """
    if not validate:
        validate=lambda selection: len(selection) >= 1
    result= inquirer.checkbox(
        message=msg,
        choices=choices,
        default=default,
        mandatory=mandatory,
        validate=validate,
        instruction=instruction,
        transformer=transformer
    )
    if sync:
        return result.execute()
    return result.execute_async()


"""
Provides a prompt to enter a string
:params msg: msg to print on menu
:params default: choice to highlight on init
: params multiline: enable multiple lines of input
:instructions: Advanced instructions for multiline mode
:returns any: choice selected
"""
def strinput(msg,default="",multiline=False,instructions=None,sync=True):

    if multiline and not instructions:
        instructions="Press Enter to Move to new line\nESC + Enter to Finish"
    result=inquirer.text(message=msg,default=default,multiline=multiline,instruction=instructions)
    if sync:
        return result.execute()
    return result.execute_async()



