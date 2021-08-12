# !!!PRZEDEWSZYSTKIM!!!
# ZROBIĆ BACKUP /usr/lib/x86_64-linux-gnu/cinnamon-settings-daemon/csd-xsettings


# Pobieramy cinnamon-settings-daemon w celu kompilacji (dla mint 20: https://github.com/linuxmint/cinnamon-settings-daemon) i kopiujemy do /opt
# W pliku /opt/cinnamon-settings-daemon-master/plugins/xsettings/csd-xsettings-manager.c  zmieniamy wartośc DPI_FALLBACK np na 144 (daje to nam skalę 1.5=144/96, gdzie 96 to default)
# Pobrać dependencies i skompilować. 

# Terminal step by step:

# cd /opt/cinnamon-settings-daemon-master/
# sudo vim ./plugins/xsettings/csd-xsettings-manager.c # zmieniamy DPI_FALLBACK
# # Instalujemy dependencies
# sudo apt-get install -y libcinnamon-desktop-dev liblcms2-dev intltool glib2.0 libtool cinnamon-desktop-environment gtk+-3.0 libnotify-dev libgnomekbd-dev libxklavier-dev libcanberra-dev libcvc-dev libupower-glib-dev libcanberra-gtk3-dev libcolord-dev libnss3-dev libcups2-dev meson debhelper-compat libdbus-glib-1-dev libgudev-1.0-dev libpolkit-gobject-1-dev librsvg2-dev libsystemd-dev libwacom-dev docbook-xsl libcinnamon-desktop-dev xsltproc
# sudo dpkg-buildpackage -i
# sudo dpkg -i ../cinnamon-settings-daemon-dev_5.0.4_amd64.deb


#############
##   LUB   ##
#############

#getCsd.py:
import os
import shutil

rootPath = '/opt/cinnamon-settings-daemon-master/plugins'
libDir = '.libs'
# copyDestination = '/usr/lib/x86_64-linux-gnu/cinnamon-settings-daemon'
os.mkdir('new_libs')
copyDestination = 'new_libs'
libToCopyPathList = []
libToCopyNameList = []
# Agregacja sciezek do plikow ktorych poszukujemy
for pluginDir in os.listdir(rootPath):
	pluginLibDir = os.path.join(rootPath, pluginDir, libDir)
	if not os.path.exists(pluginLibDir):
		continue
	liblibNameList = os.listdir(pluginLibDir)
	for libName in liblibNameList:
		if libName.startswith('csd-'):
			libPath = os.path.join(pluginLibDir, libName)
			if libPath not in libToCopyPathList:
				libToCopyNameList.append(libName)
				libToCopyPathList.append(libPath)
# Kopiowanie wybranych libek do zdefiniowanego katalogu copyDestination
if libToCopyPathList:
	# usuwamy stare libki (czyscimy)
	for libName in libToCopyNameList:
		oldLibPath = os.path.join(copyDestination, libName)
		if os.path.exists(oldLibPath):
			os.remove(oldLibPath)
	# kopiujemy nowe libki
	for libToCopy in libToCopyPathList:
		shutil.copy2(libToCopy, copyDestination)
