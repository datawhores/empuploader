@echo off

REM 1. Install MinGW x64:
REM
REM - Download mingw-w64-install.exe from http://mingw-w64.org/doku.php/download/mingw-builds
REM - During the installation process change
REM    - Architecture to x86_64
REM    - Destination folder do C:\mingw64
REM
REM
REM 2. Install FFmpeg and libGD:
REM
REM - Download the dependency ZIP files:
REM     - FFmpeg (choose prefered version with "shared" in filename) from https://github.com/BtbN/FFmpeg-Builds/releases/
REM     - libGD (Nuget package) from https://ci.appveyor.com/api/buildjobs/ftll74ieg5l0hr2i/artifacts/libgd-mingw-x64-master.2.1.1.219.nupkg
REM - Extract dirs/files using 7-zip
REM       libgd-mingw-x64-master.2.1.1.219.nupkg\*.h => C:\mingw64\mingw64\include
REM       libgd-mingw-x64-master.2.1.1.219.nupkg\*.a => C:\mingw64\mingw64\lib
REM       libgd-mingw-x64-master.2.1.1.219.nupkg\*.dll => C:\mingw64\mingw64\bin
REM       ffmpeg-n4.3.1-221-gd08bcbffff-win64-lgpl-shared-4.3.zip\ffmpeg*\include => C:\mingw64\mingw64\include
REM       ffmpeg-n4.3.1-221-gd08bcbffff-win64-lgpl-shared-4.3.zip\ffmpeg*\lib => C:\mingw64\mingw64\lib
REM       ffmpeg-n4.3.1-221-gd08bcbffff-win64-lgpl-shared-4.3.zip\ffmpeg*\bin => C:\mingw64\mingw64\bin
REM - Verify you unzipped the files correctly.
REM   If you unzipped correctly you should now see avcodec.h in C:\mingw64\mingw64\include\libavcodec\avcodec.h
REM
REM    `-- C:
REM        |-- mingw64
REM            |`-- mingw64
REM                |-- bin
REM                |   |-- avcodec-58.dll
REM                |   |-- gcc.exe
REM                |   |-- liblibgd.dll
REM                |   `-- swscale-5.dll
REM                |-- include
REM                |   |-- gd.h
REM                |   |-- gd_io.h
REM                |   |-- gdfx.h
REM                |   |-- libavcodec
REM                |   |   `-- avcodec.h
REM                |   |-- libavdevice
REM                |   |   |-- avdevice.h
REM                |   |   `-- version.h
REM                |   |-- libswresample
REM                |   |   |-- swresample.h
REM                |   |   `-- version.h
REM                |   `-- libswscale
REM                |       |-- swscale.h
REM                |       `-- version.h
REM                `-- lib
REM                    |-- libavcodec.dll.a
REM                    |-- libavdevice.dll.a
REM                    |-- libavfilter.dll.a
REM                    |-- libavformat.dll.a
REM                    |-- libavutil.dll.a
REM                    |-- liblibgd.a
REM                    |-- liblibgd.dll.a
REM                    |-- libswresample.dll.a
REM                    |-- libswscale.dll.a
REM                    |-- swresample.lib
REM                    `-- swscale.lib
REM
REM
REM 3. Build MTN by running this script
REM    C:\..\mtn\src> Make.MinGW.bat
REM
REM 4. To run MTN you need 
REM    - either add "C:\mingw64\mingw64\bin" to your PATH environment variable
REM    - or copy dependent libraries from C:\mingw64\mingw64\bin and place in the same folder as mtn.exe
REM
REM   dependent libraries are now located here:
REM   (note: numbered suffix depends on FFmpeg version)
REM     C:\mingw64\mingw64\bin\avcodec-58.dll
REM     C:\mingw64\mingw64\bin\avformat-58.dll
REM     C:\mingw64\mingw64\bin\avutil-56.dll
REM     C:\mingw64\mingw64\bin\swresample-3.dll
REM     C:\mingw64\mingw64\bin\swscale-5.dll
REM     C:\mingw64\mingw64\bin\liblibgd.dll

set MINGWDIR=C:\mingw64\mingw64
set PATH=%MINGWDIR%\bin;%PATH%

set CC=gcc
set CFLAGS=-Wall -DWIN32 -O3

set LDFLAGS=-L%MINGWDIR%\lib
set INCLUDE=-I%MINGWDIR%\include
set LIBS=-llibgd -lavutil -lavdevice -lavformat -lavcodec  -lswscale

if not exist "..\bin\" mkdir "..\bin"
%CC% -o ../bin/mtn mtn.c %CFLAGS% %LDFLAGS% %INCLUDE% %LIBS%
