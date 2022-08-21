
pdf_invoice(){
if [[ $1 == "-h" ]] || [[ $1 == "-help" ]] || [[ $1 == "--help" ]] || [[ $# -eq 0 ]];
then
    echo -e "\e[1;30;47mpdf_invoice file [OPTIONS]\e[0m         extract 1st page of file and optimize it"
    echo -e "\e[1;30;43m[OPTIONS]\e[0m"
    echo -e "\e[1;30;47m-a\e[0m                                 split ALL pages to diferent files"
    echo -e "\e[1;30;47m-c\e[0m                                 start krop GUI to crop selected area of PDF"
    echo -e "\e[1;30;47m-o\e[0m                                 optimize and compress PDF file using ghostscript after all"
else
    # Rozdzielenie stron na pliki
    SP_DIR=tmp
    rm -rf ${SP_DIR} 2>/dev/null
    mkdir -p ${SP_DIR}
    DO_SPLIT_ALL=false
    DO_KROP_PDF=false
    DO_OPTIMIZE_PDF=false
    lastMonthYear=$(date --date="-1 month" +"%m.%Y")
    inputPdf=""
    # FILES_ARRAY=("")
    declare -a FILES_ARRAY
    for option in "$@"
    do  
      if [ "$option" = "-a" ];
      then
        DO_SPLIT_ALL=true
      elif [ "$option" = "-c" ];
      then
        DO_KROP_PDF=true
      elif [ "$option" = "-o" ];
      then
        DO_OPTIMIZE_PDF=true
      elif [ "${option##*.}" = "pdf" ]
      then
        # Dodanie nazwy pliku do szeregu
        # echo "option: $option"
        # Escapeowanie
        # FILENAME=$(printf %q "$option")
        # echo "filename: $FILENAME"
        # FILES_ARRAY=(${FILES_ARRAY[@]} "$FILENAME")
        FILES_ARRAY+=("$option")
      fi  
    done

    # TODO - debuggowanie
    # for i in "${FILES_ARRAY[@]}"
    # do
    #   echo "echo array objs: $i"
    # done


    if [ ${#FILES_ARRAY[@]} -eq 0 ]
    then
      echo -e "\e[1;41m[ERROR]\e[0m Files array is empty"
      exit 0 
    fi

    # echo "input path: " $inputPdf
    for FILE in "${FILES_ARRAY[@]}"
    do      
      fname="${FILE##*/}" 

      # Podzielenie pdf wielostronicowego na pojedyncze pliki
      if $DO_SPLIT_ALL;
      then
        pdftk "$FILE" burst output "${SP_DIR}/%02d_${fname}"
        echo -e "\e[93m\e[1mEXTRACT ALL PAGE OF:\e[0m   ${fname}"   
      else
        pdftk "$FILE" cat 1 output "${SP_DIR}/${fname}"        
        echo -e "\e[93m\e[1mEXTRACT 1ST PAGE OF:\e[0m   ${fname}"   
      fi
      rm -f "${SP_DIR}"/doc_info.txt 2>/dev/null
    done


    # Wycinanie white space narzędziem KROP
    if $DO_KROP_PDF;
    then
      for file in "${SP_DIR}"/*.pdf
      do
	    echo "kroping: $file"
        sudo krop "$file" -o "${SP_DIR}/paliwo_.${lastMonthYear}.pdf"
        rm $file
      done
    fi

    #output dir
    OP_DIR=pdf_so
    mkdir -p ${OP_DIR}    
    for file in ${SP_DIR}/*.pdf
    do
      fname="${file##*/}"
      echo -e "\e[93m\e[1mOUTPUT:  \e[0m\e[92m${fname}\e[0m"
      # Włączona optymalizacja dodatkowa
      if $DO_OPTIMIZE_PDF;
      then
          pdf_optimize "${file}" "${OP_DIR}"/"${fname}"
      else
          cp "${file}" "${OP_DIR}"/"${fname}"
      fi
    done
    rm -f doc_data.txt 2>/dev/null
    rm -rf "${SP_DIR}" 2>/dev/null
    echo -e "\e[1;237;42m[DONE]\e[0m"
fi  
}

pdf_optimize(){
    gs -q -dNOPAUSE -dBATCH -dSAFER -dPDFA=2 -dPDFACompatibilityPolicy=1 -dSimulateOverprint=true -sDEVICE=pdfwrite -dCompatibilityLevel=1.3 -dPDFSETTINGS=/screen -dEmbedAllFonts=true -dSubsetFonts=true -dAutoRotatePages=/None -dColorImageDownsampleType=/Subsample -dColorImageResolution=200 -dGrayImageResolution=200 -dColorImageDownsampleType=/Bicubic -dMonoImageResolution=200 -sOutputFile=${2} ${1}
}
