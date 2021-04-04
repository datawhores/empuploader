#  project for building and debuging with QT-Creator

TEMPLATE = app
TARGET = mtn
INCLUDEPATH += .
INCLUDEPATH += /usr/include/ffmpeg
INCLUDEPATH += /usr/include
LIBS += -L/usr/lib64 -lavcodec -lavformat -lavcodec -lswscale -lavutil -lgd

HEADERS += fake_tchar.h
SOURCES += mtn.c

DISTFILES += \
    Make.MinGW.bat
