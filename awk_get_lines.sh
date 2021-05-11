#!/bin/bash
trace_error(){
  echo -e "\e[1;41m[ERROR]\e[0m $1"
}


trace_info(){
  echo -e "\e[1;30;47m[INFO]\e[0m $1"
}

awk_get_lines(){
  if [ $# -lt 3 ] 
  then
    trace_error "WRONG USAGE"
    trace_info "Usage: awk_get_lines <file_name> <start_line> <end_line>"
    exit 1
  else
    awk 'NR >= $2 && NR <= $3' "${1}"
  fi;
}
