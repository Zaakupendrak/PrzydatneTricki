# 1. Backup

```shell
mkdir -p ~/Desktop/csd_backup/
cp /usr/libexec/csd-* ~/Desktop/csd_backup/
```

# 2. Źródła
```shell
cd ~/Downloads
wget https://github.com/linuxmint/cinnamon-settings-daemon/archive/refs/heads/master.zip
unzip master.zip -d .
rm master.zip
```

Do pobrania stąd: 
https://github.com/linuxmint/cinnamon-settings-daemon

# 3. Edycja DPI_FALLBACK
Np wartość 136 daje to nam skalę 1.38=136/96, gdzie 96 to default.
```shell
vim cinnamon-settings-daemon-master/plugins/xsettings/csd-xsettings-manager.c
```

# 4. Kompilacja
```shell
cd cinnamon-settings-daemon-master
#dpkg-buildpackage - powie jakich dependenciesów brakuje
sudo apt update
sudo apt install -y cmake gcc-multilib libcanberra-gtk3-dev libtool cinnamon-desktop-environment libgtk3.0-cil-dev libnotify-dev libgnomekbd-dev libxklavier-dev libcanberra-dev libcvc-dev libupower-glib-dev libcanberra-gtk3-dev libcolord-dev libnss3-dev libcups2-dev
sudo apt install -y docbook-xsl intltool libcinnamon-desktop-dev libgudev-1.0-dev liblcms2-dev libpolkit-gobject-1-dev librsvg2-dev libsystemd-dev libwacom-dev xsltproc debhelper
meson build/  
ninja -C build/
```

# 5. Podmiana libek
Należy wejść w konsolę bez GUI, np CTLR+ALT+F1 
```
sudo service lightdm stop
sudo cp /home/zaak/Downloads/cinnamon-settings-daemon-master/build/plugins/xsettings/csd-xsettings /usr/libexec
sudo service lightdm start
```




# Programik do kopiowania wszystkich csd-* do sourceDir.
```python
import os
import shutil

rootPath = '/home/sjakubowski/Downloads/cinnamon-settings-daemon-master/build/plugins'
destDir = '.libs'
try:
	shutil.rmtree(destDir)
except:
	print("$destDir do not exists")
# copyDestination = '/usr/lib/x86_64-linux-gnu/cinnamon-settings-daemon'
try:
	os.mkdir(destDir)
except:
	rint("$destDir already exists")
	
copyDestination = destDir
libToCopyPathList = []
libToCopyNameList = []
# Agregacja sciezek do plikow ktorych poszukujemy
for pluginDir in os.listdir(rootPath):
	print("dir: " + pluginDir)
	pluginLibDir = os.path.join(rootPath, pluginDir)
	if not os.path.exists(pluginLibDir):
		continue
	liblibNameList = os.listdir(pluginLibDir)
	for libName in liblibNameList:
		if libName.startswith('csd-') and '.' not in libName:
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
		print("copying: " + libToCopy)
		shutil.copy2(libToCopy, copyDestination)
```
	
