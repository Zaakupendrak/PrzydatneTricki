pdf_extract(){
    pdftk $1 cat $2 output "e_$1"
}

pdf_split_optimize(){
if [[ $1 == "-h" ]] || [[ $1 == "-help" ]] || [[ $1 == "--help" ]] || [[ $# -eq 0 ]];
then
    echo -e "\e[36mpdf_split_optimize \e[3m\e[1mfilePath\e[0m               splits and optimize only first page of file in filePath"
    echo -e "\e[36mpdf_split_optimize \e[3m\e[1mdirPath\e[0m                splits and optimize only first pages of files in dirPath/*.pdf files"  
    echo -e "\e[36mpdf_split_optimize \e[3m\e[1mfilePath/dirPath -a\e[0m    flag enables splitting all pages of document; otherwise script extracts only first pages"   
else
    # Rozdzielenie stron na pliki
    SP_DIR=tmp
    mkdir -p ${SP_DIR}
    fname="${1##*/}"
    echo -e "\e[93m\e[1mINPUT:\e[0m   ${fname}"
    if [ "$2" = "-a" ];
    then
            pdftk "$1" burst output "${SP_DIR}/%02d_${fname}"
    else
            pdftk "$1" cat 1 output "${SP_DIR}/${fname}"
    fi
    rm -f ${SP_DIR}/doc_info.txt

    # Optymalizacja/kompresja
    OP_DIR=pdf_so
    mkdir -p ${OP_DIR}
    for file in ${SP_DIR}/*.pdf
    do        
        fname="${file##*/}"
        echo -e "\e[93m\e[1mOUTPUT:  \e[0m\e[92m${fname}\e[0m"
        # Wyłączone verbose
        #pdf_optimize ${file} ${OP_DIR}/${fname}
	cp ${file} ${OP_DIR}/${fname}
    done
    rm -f doc_data.txt
    rm -rf ${SP_DIR}
fi
}

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
    fname="${1##*/}"
    echo -e "\e[93m\e[1mINPUT:\e[0m   ${fname}"
    splitAll=false
    kropPdf=false
    optimizePdf=false
    lastMonthYear=$(date --date="-1 month" +"%m.%Y")
    inputPdf=""
    for option in $@
    do  
        if [ "$option" = "-a" ];
        then
            splitAll=true
        elif [ "$option" = "-c" ];
        then
            kropPdf=true
        elif [ "$option" = "-o" ];
        then
            optimizePdf=true
        elif [ "${option##*.}" = "pdf" ]; 
	then
            inputPdf="$option"
        fi  
    done

    echo $inputPdf
    echo "$inputPdf"
    if [ $inputPdf = "" ];
    then
        echo -e "\e[1;41m[ERROR]\e[0m No pdf file provided"
        exit 0 
    fi

    # Podzielenie pdf wielostronicowego na pojedyncze pliki
    if $splitAll;
    then
        pdftk $inputPdf burst output "${SP_DIR}/%02d_${fname}"
        echo "split all"
    else
        pdftk $inputPdf cat 1 output "${SP_DIR}/${fname}"
    fi
    rm -f ${SP_DIR}/doc_info.txt 2>/dev/null


    # Wycinanie white space
    if $kropPdf;
    then
        for file in ${SP_DIR}/*.pdf
        do
            sudo krop $file -o "${SP_DIR}/paliwo_.${lastMonthYear}.pdf"
            rm $file 2>/dev/null
        done
    fi


    OP_DIR=pdf_so
    mkdir -p ${OP_DIR}    
    for file in ${SP_DIR}/*.pdf
    do
        fname="${file##*/}"
        echo -e "\e[93m\e[1mOUTPUT:  \e[0m\e[92m${fname}\e[0m"
        # Wyłączone verbose
        if $optimizePdf;
        then
            pdf_optimize ${file} ${OP_DIR}/${fname}
        else
            cp ${file} ${OP_DIR}/${fname}
        fi
    done
    rm -f doc_data.txt
    rm -rf ${SP_DIR}
    echo -e "\e[1;237;42m[DONE]\e[0m"
fi
}

pdf_optimize(){
    gs -q -dNOPAUSE -dBATCH -dSAFER -dPDFA=2 -dPDFACompatibilityPolicy=1 -dSimulateOverprint=true -sDEVICE=pdfwrite -dCompatibilityLevel=1.3 -dPDFSETTINGS=/screen -dEmbedAllFonts=true -dSubsetFonts=true -dAutoRotatePages=/None -dColorImageDownsampleType=/Subsample -dColorImageResolution=200 -dGrayImageResolution=200 -dColorImageDownsampleType=/Bicubic -dMonoImageResolution=200 -sOutputFile=${2} ${1}
}
