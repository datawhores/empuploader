
# EmpUploader

**EmpUploader** is a Python script that automates the process of uploading image or video thumbnail files to image hosting services, or torrent files to specific platforms. The script provides functionalities such as file preparation, editing, previewing, and uploading.

## Features

- **File Preparation**: Scans a folder/file and prepares data required for upload.
- **Editing**: Modify details before uploading.
- **Preview**: Review uploads before proceeding.
- **Uploading**: Upload files or torrents to the specified platform.

## Installation

### Requirements
- Python 3.6 or higher

### Linux
1. Clone the repository:
   ```bash
   git clone https://github.com/excludedBittern8/empuploader
   ```
2. Navigate to the directory:
   ```bash
   cd empuploader
   ```
3. Set up a virtual environment:
   ```bash
   python3 -m pip install --user virtualenv
   python3 -m venv env
   source env/bin/activate
   which python  # Should point to the virtualenv
   ```
4. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   pip install imageio[ffmpeg]
   ```
5. For Linux, ensure binary permissions:
   ```bash
   chmod +x -R ./bin/
   deactivate  # After installing the requirements
   ```

### Chrome 
  - (Manual Install of a current chromium binary requires sudo Alternatively you can allow empuploader to install a hardcoded version of chromium automatically):
   ```bash
   pip install playwright
   playwright install chromium
   ```
Don't have sudo?
Don't worry the script will auto download a portable version of chromium for you

### Windows
1. Clone the repository:
   ```bash
   git clone https://github.com/excludedBittern8/empuploader
   cd empuploader
   ```
2. Set up a virtual environment:
   ```bash
   py -3 -m pip install --user virtualenv
   py -3 -m venv env
   .\env\Scripts\activate
   which python  # Should point to the virtualenv
   py -3 -m pip install -r requirements.txt
   pip install imageio[ffmpeg]
   playwright install chromium
   deactivate  # After installing the requirements
   ```

## Running the Program

### Setup
- **Linux**: 
  ```bash
  source env/bin/activate
  ```
- **Windows**: 
  ```bash
  .\env\Scripts\activate
  ```

### Modes
1. **Prepare Mode**: Scans a folder/file and prepares the data for upload (mandatory step).
2. **Edit Mode**: Edit details before uploading.
3. **Preview Mode**: Preview uploads.
4. **Upload Mode**: Upload files or torrents.

### Commands/Arguments
- Detailed examples and command usage can be found in the [Wiki](https://github.com/excludedBittern8/empuploader/wiki).
- Detailed arguments to pass can be found in the [wiki/commands-and-args](https://github.com/excludedBittern8/empuploader/wiki/commands-and-args).

## Contributions

Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

