#!/usr/bin/env sh
HYPRGAMEMODE=$(hyprctl getoption general:gaps_in | awk 'NR==2{print $2}')
if [ "$HYPRGAMEMODE" = 6 ] ; then
 hyprctl --batch "\
     keyword general:gaps_in 0;\
     keyword general:gaps_out 0;\
     keyword general:border_size 0;\
     keyword decoration:rounding 0"
 exit
else
 hyprctl --batch "\
     keyword general:gaps_in 6;\
     keyword general:gaps_out 12;\
     keyword general:border_size 1;\
     keyword decoration:rounding 8"
fi
