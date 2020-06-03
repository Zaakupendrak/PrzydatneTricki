# Musisz mieć zainstalowany cinnamon-settings-daemon-master, np w /opt

# W katalogu: 
# /opt/cinnamon-settings-daemon-master/plugins/ 
# należy znależć 
# ./plugins/xsettings/csd-xsettings-manager.c  
# i wyedytować DPI_FALLBACK na wybraną przez siebie wartość.
# Później skompilować i skopiować biblioteki do 
# /usr/lib/x86_64-linux-gnu/cinnamon-settings-daemon/csd-xsettings
# pamietaj o backupie.

# cd /opt/cinnamon-settings-daemon-master/
# sudo vim ./plugins/xsettings/csd-xsettings-manager.c 
# sudo make clean
# sudo make install
# sudo python /home/zaak/Desktop/newCsd.py 



#newCsd.py:

import os
import shutil

rootPath = '/opt/cinnamon-settings-daemon-master/plugins'
libDir = '.libs'
copyDestination = '/usr/lib/x86_64-linux-gnu/cinnamon-settings-daemon'
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
