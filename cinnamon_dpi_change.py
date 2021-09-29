# !!!PRZEDEWSZYSTKIM!!!
# ZROBIĆ BACKUP libek csd, dla Mint 20 w 


# Pobieramy cinnamon-settings-daemon w celu kompilacji, dla mint 20: https://github.com/linuxmint/cinnamon-settings-daemon
# W pliku dir/cinnamon-settings-daemon-master/plugins/xsettings/csd-xsettings-manager.c  zmieniamy wartośc DPI_FALLBACK np na  wybraną przez siebie; 
# np 144 daje to nam skalę 1.5=144/96, gdzie 96 to default.

# UWAGA #
# Dla najnowsza wersji cinnamon czyli 5.0.5, cinnamon-settings-daemon korzysta z mesona do kompilacji
# Terminal step by step:
# meson build/          - sprawdza dependenciesy
# ninja -C build/	- kompiluje do katalogu build w rootcie paczki




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
