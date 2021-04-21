#Make prompt colored for sjakubowski
if [ "$SSH_CONNECTION" != "" ];
then
  IFS=' '
  read -a strarr <<< "$SSH_CONNECTION"
  SSH_IP=${strarr[0]}
  echo -e "[\e[94mSJA Logged in\e[0m] from = $SSH_IP"
  if [ "$SSH_IP" = "10.92.32.61" ] || [ "$SSH_IP" = "10.92.2.84" ];
  then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;33m\]\u@\h\[\033[00m\]:\[\033[1;38;5;246m\]\w\[\033[00m\]\$ '
  fi;
fi;
