#!/bin/bash

# Set directory to wallpaper folder
dir="$HOME/Pictures/Wallpapers"

# Create array of images in directory
images=( $(ls $dir) )

# Use Rofi to display image selection menu
selected=$(printf '%s\n' "${images[@]}" | rofi -dmenu -p "Select wallpaper image")

# If user selects an image, run command with selected image as argument
if [[ -n $selected ]]; then
  swww img "$dir/$selected" --transition-fps 60 --transition-type any --transition-duration 1
fi
