is_error(){
  if [[ "$1" =~ "ie ustawiono" ]] || [[ "$1" =~ "error" ]] || [[ "$1" =~ "Error" ]] || [[ "$1" =~ "ERROR" ]] || [[ "$1" =~ "not found" ]] || [[ "$1" =~ "undefined reference" ]] ;
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
  # if [[ $1 =~ "arning" ]] || [[ $1 =~ "ARNING" ]] ;
  if [[ $1 =~ "WARNING" ]] ;
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
    if is_warn "$1" || is_error "$1"; then
        return 0 # true
    else
        return 1 # false
    fi
}


color()(
  NC='\033[0m'
  set -o pipefail; export MSG=$("$@" 2>&1>&3);
  #echo "MSG: $MSG"
  CURR_COLLOR='\033[0m'
  while IFS= read -r line; do
    # setup color for block
    if is_new_warn_error "$line"; then
        if [ "$CURR_COLLOR" != "$CM" ]; then
          CURR_COLLOR=$CM
        else
          CURR_COLLOR=$CL
        fi
    fi    
    echo -e "${CURR_COLLOR}${line}${NC}">&2
  done <<< "$MSG"
)3>&1
