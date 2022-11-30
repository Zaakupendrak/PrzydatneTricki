is_error(){
  #shopt -s nocasematch # set case insensitive search
  if egrep -iq  '(\sno rule|error\s|\serror|nie\sustawiono|not\sfound|undefined\sreference)' <<< $1 ; 
  # if [[ "$1" =~ "nie ustawiono" ]] || [[ "$1" =~ "error" ]] || [[ "$1" =~ "Error" ]] || [[ "$1" =~ "ERROR" ]] || [[ "$1" =~ "not found" ]] || [[ "$1" =~ "undefined reference" ]] ;
  then
    export CM='\033[1;91m' # bold light red
    export CL='\033[38;2;255;150;0m' # orange
    # export CL='\033[0;91m' # dark red
    return 0 # true
  else
    return 1 # false
  fi
}


is_warn(){
  #shopt -s nocasematch # set case insensitive search
  # if [[ $1 =~ "arning" ]] || [[ $1 =~ "ARNING" ]] ;
  if egrep -iq  'warning' <<< $1 ;
  then
    # export CM='\033[1;33m' # bold yellow
    # export CL='\033[0;33m' # brown
    # export CM='\033[1;35m' # bold ligh purple
    export CM='\033[38;2;221;160;221m' # plum
    # export CL='\033[38;2;218;112;214m' # fuchsia
    export CL='\033[38;2;147;112;219m' # mediumpurple
    # export CL='\033[95;7m' # purple backgorund
    return 0 # true
  else
    return 1 # false
  fi
}


is_new_warn_error(){
    if is_warn "$1" ; then
      return 0 # true
    elif is_error "$1" ; then
      return 0 # true
    else
      return 1 # false
    fi
}


color()(
  NC='\033[0m' #no color
  
  set -o pipefail 
  # set -o pipefail prevents errors in a pipeline from being masked. 
  # If any command in a pipeline fails, that return code will be used as the return code of the whole pipeline.


  export MSG=$("$@" 2>&1>&3) # redirects STDERR to STDOUT  and STDOUT to temporary file descriptor 3
  
  CURR_COLLOR='\033[0m'
  while IFS= read -r line; do
    # setup color for block
    if is_new_warn_error "$line"; then
        if [ "$CURR_COLLOR" != "$CM" ]; then
          CURR_COLLOR=$CM
        else
          CURR_COLLOR=$CL
        fi
    # elif egrep -iq 'kompilacja' <<< $1 ; then 
    #   CURR_COLLOR='\033[38;2;34;139;34m' #green
    fi
    echo -e "${CURR_COLLOR}${line}${NC}" #>&2
  done <<< "$MSG"
)3>&1 # bring back original STDOUT from file descriptor 3


alias make='color make'
