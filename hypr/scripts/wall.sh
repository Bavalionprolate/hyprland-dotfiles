#!/bin/bash

# Устанавливаем директорию с обоями
dir="$HOME/Pictures/Wallpapers"

# Создаем массив изображений и видеофайлов в директории
images=( $(find "$dir" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" \)) )
videos=( $(find "$dir" -type f \( -iname "*.mp4" -o -iname "*.webm" -o -iname "*.mkv" \)) )

# Объединяем изображения и видео в один массив и добавляем маркер (Image/Video)
entries=()
for img in "${images[@]}"; do
    entries+=("Image: $(basename "$img")")
done
for vid in "${videos[@]}"; do
    entries+=("Video: $(basename "$vid")")
done

# Отображаем меню Rofi для выбора обоев
selected=$(printf '%s\n' "${entries[@]}" | rofi -dmenu -p "Select wallpaper")

# Проверяем, было ли сделано какое-либо действие
if [[ -n $selected ]]; then

    file_type=$(echo "$selected" | cut -d':' -f1)
    file_name=$(echo "$selected" | cut -d':' -f2 | xargs)

    pkill -f mpvpaper

    if [[ $file_type == "Image" ]]; then
        swww img "$dir/$file_name" --transition-fps 100 --transition-type any --transition-duration 0.4
    elif [[ $file_type == "Video" ]]; then
        mpvpaper -o "no-audio --loop-playlist shuffle" '*' "$dir/$file_name"

    fi
fi
