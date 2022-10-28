for f in ipay*.manifest; do cp "$f" "$(echo "$f" | sed s/.manifest/_rh8.manifest/)"; done
