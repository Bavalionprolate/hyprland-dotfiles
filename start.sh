#!/bin/sh

export QT_AUTO_SCREEN_SCALE_FACTOR=1
export LIBVA_DRIVER_NAME=nvidia
export XDG_SESSION_TYPE=wayland
export QT_QPA_PLATFORM=wayland;xcb
export GBM_BACKEND=nvidia-drm
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export WLR_RENDER=vulkan
export WLR_NO_HARDWARE_CURSORS=1
export MOZ_ENABLE_WAYLAND=1

exec Hyprland
