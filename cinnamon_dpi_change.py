# !!!PRZEDEWSZYSTKIM!!!
# ZROBIĆ BACKUP libek csd, z konsoli "cp /usr/libexec/csd-* ~/Desktop/csd_backup/"
# Dla Mint 20 w /usr/lib/x86_64-linux-gnu/cinnamon-settings-daemon/ są tylko symlinki do csd-* zainstalowanych w /usr/libexec
# Po zainstalowaniu nowo skompilowanego csd-xsettings w /usr/libexec możliwe że nalezy poprawic symlinki.
# Instalacja skompilowanych libek bedzie problematyczna z powodu działających/restartujących się procesów. 
# Mozna to zrobić bez działającego serwera x logując się do konsoli (CTRL+ALT+F2)
# sudo service lightdm stop
# sudo cp /home/sjakubowski/Downloads/cinnamon-settings-daemon-master/build/plugins/xsettings/csd-xsettings /usr/libexec
# sudo service lightdm start


# Pobieramy cinnamon-settings-daemon w celu kompilacji, dla mint 20: https://github.com/linuxmint/cinnamon-settings-daemon
# W pliku dir/cinnamon-settings-daemon-master/plugins/xsettings/csd-xsettings-manager.c  zmieniamy wartośc DPI_FALLBACK np na  wybraną przez siebie; 
# np 144 daje to nam skalę 1.5=144/96, gdzie 96 to default.

# UWAGA #
# Dla najnowsza wersji cinnamon czyli 5.0.5, cinnamon-settings-daemon korzysta w kompilacji z meson/ninja (spoko sprawa)
# Terminal step by step:
# meson build/          - sprawdza dependenciesy
# ninja -C build/	- kompiluje do katalogu build w rootcie paczki






# Programik do kopiowania wszystkich csd-* do sourceDir.
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
