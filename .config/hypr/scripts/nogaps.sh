#!/usr/bin/env sh
HYPRGAMEMODE=$(hyprctl getoption general:gaps_in | awk 'NR==2{print $2}')
if [ "$HYPRGAMEMODE" = 6 ] ; then
    hyprctl --batch "\
        keyword decoration:drop_shadow 0;\
        keyword general:gaps_in 0;\
        keyword general:gaps_out 0;\
        keyword general:border_size 0;\
        keyword decoration:rounding 0"
    exit
fi
hyprctl reload
