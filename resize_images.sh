#!/bin/bash

# ZMienia rozmiar zdjecia procentowo oraz ustawia maksymalny mozliwy rozmiar pliku 
for FILE in *; 
do
  mkdir -p resized
  # convert $FILE -resize 90%x90% resized/$FILE
  convert $FILE -resize 90%x90% -define jpeg:extent=5000kb resized/$FILE  
  echo "$FILE processed"; 
done
