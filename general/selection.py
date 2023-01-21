from InquirerPy import inquirer
def singleoptions(msg,choices,default=None):
     return inquirer.select(
        message=msg,
        choices=choices,
        default=default,
    ).execute()

def strinput(msg,default="",multiline=False,instructions=None):
    if multiline and not instructions:
        instructions="Press Enter to Move to new line\nESC + Enter to Finish"
    return inquirer.text(message=msg,default=default,multiline=multiline,instruction=instructions).execute()
  
  

