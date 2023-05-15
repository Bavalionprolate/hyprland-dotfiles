#!/bin/sh

export LIBVA_DRIVER_NAME=nvidia
export XDG_SESSION_TYPE=wayland
export QT_QPA_PLATFORM=wayland
export GBM_BACKEND=nvidia-drm
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export WLR_RENDER=vulkan
export WLR_NO_HARDWARE_CURSORS=1

exec Hyprland
