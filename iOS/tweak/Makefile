include $(THEOS)/makefiles/common.mk


TWEAK_NAME = appstore_auto_downloader
TARGET = iphone:latest:8.0
appstore_auto_downloader_FILES = Tweak.xm XMAutoDownloader.m XMDownladTask.m
appstore_auto_downloader_EXTRA_FRAMEWORKS = PTFakeTouch
appstore_auto_downloader_FRAMEWORKS = UIKit IOKit CoreGraphics CydiaSubstrate 
appstore_auto_downloader_LIBRARIES = applist
appstore_auto_downloader_LDFLAGS = -Wl,-segalign,4000

include $(THEOS_MAKE_PATH)/tweak.mk

after-install::
	install.exec "killall -9 SpringBoard installd itunesstored"
