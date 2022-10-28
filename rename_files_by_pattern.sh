for f in *.jpg; do mv "$f" "$(echo "$f" | sed s/IMG/VACATION/)"; done
#In this example, I am assuming that all your image files contain the string IMG and you want to replace IMG with VACATION.
