from InquirerPy import inquirer
"""
Provides a menu limited by one choice
:params msg: msg to print on menu
:params choices: list of choices to pick from
:params default: choice to highlight on init
:returns any: choice selected
"""
def singleoptions(msg,choices,default=None):
     return inquirer.select(
        message=msg,
        choices=choices,
        default=default,
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
  
  

