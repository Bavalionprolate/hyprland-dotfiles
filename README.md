# Hyprland Dotfiles

This repository contains dotfiles for Hyprland, a custom desktop environment built on Arch Linux. These dotfiles enhance the appearance and functionality of Hyprland.

## Installation

To use these dotfiles, follow these steps:

1. Clone the repository:

~~~
git clone https://gitlab.com/BA_usr/dotfiles-for-hyperland.git
~~~

2. Navigate to the cloned directory:

~~~
cd dotfiles-for-hyperland
~~~

3. Install the required packages:

~~~
yay -S ttf-twemoji waybar kitty ttf-jetbrains-mono-nerd pavucontrol jq nvidia-settings libnotify dunst slurp grim wl-clipboard xdg-desktop-portal-hyprland libcanberra wireless_tools pamixer xdg-user-dirs blueberry wlrobs-hg hyprshade greetd greetd-gtkgreet cage
~~~

4. Move the `.fonts` directory to your home folder and all contents from `.config` to your local `config` directory. If you want to use dark icons like mine, move the `.icons` folder to your home directory.

5. Customize the dotfiles according to your preferences.

## Features

##### Hyprland dotfiles offer the following features:

1. **Screen Capture**
  - Take a screenshot by pressing the `Print Screen` button. This allows you to select a specific area to take a screenshot.

2. **App Launcher**
  - Open the app launcher by pressing `Alt + R`. Close or exit the app launcher by clicking on an empty space on the screen or selecting an app to launch.

![App Launcher](Media/2.png)

3. **Wallpaper Management**
  - Change wallpapers by pressing `Alt + W` to open the wallpaper menu. Pressing `Meta + Shift + W` sets random wallpapers from the collection.

![Wallpaper Management](Media/3.png)

4. **Quick Settings Menu**
  - Call the quick settings menu by pressing the key combination `Alt + C`. In this menu, there is a widget for:
    - WiFi - for connecting to a network and displaying the network;
    - Bluetooth - for connecting and displaying whether it is on or off;
    - Night Color - changing the color scheme to remove blue light from the screen;
    - "Do Not Disturb" widget - turning notifications on or off;
    - Indicator showing the battery level of the last connected Bluetooth device;
    - Weather display widget;
    - Slider for switching between incoming and outgoing sound;
    - MPRIS player working on playerctl.

![Quick Settings Menu](Media/6.png)

5. **Sound Indicator**
  - This indicator displays sound when changed through:
    - The key combination `Fn + F10` and `Fn + F11`;
    - Changing through the quick settings menu manually.

This indicator works in the background and only appears when it detects changes in the volume level.

![Sound Indicator](Media/4.png)

6. **Bluetooth Menu**
  - This menu is called from the quick settings by pressing the Bluetooth button.

![Bluetooth Menu](Media/5.png)

7. **WiFi Menu**
  - This menu is called from the quick settings by pressing the WiFi button.

![WiFi Menu](Media/8.png)

8. **Application Switching**
  - Use the key combination `Meta + Tab` to switch focus between applications on the current workspace. You can also use `Meta + Arrows` for this purpose.

9. **Application Overview**
  - Use the key combination `Alt + Tab` to call the overview and view all applications on all workspaces. To switch focus in the overview, you can use the mouse or the key combinations `Meta + Arrows` or continue using `Alt + Tab`, holding `Alt` and pressing `Tab` until you release `Alt`, automatic exit from the overview will occur.
   
![Overview](Media/1.mp4)

10. **Notification Center**
   - Can be called using the key combination `Alt + B`.

![Notification Center](Media/9.png)
![Notification Center](Media/10.png)

11. **Bluetooth Indicator**

   An indicator displaying whether a device is connected and if it is connected and you have enabled the setting to display the battery, you will be able to see the battery volume. If more than one Bluetooth device is connected to your PC, the icon will change its status on the panel and stop displaying the battery volume, but to see the volume of all devices, you can click on the indicator and a window will appear displaying all devices with their statuses.

   Below is an example with one connected device:

   <img src="Media/11.png" width="900"/>

12. special workspace.

   To move an application into special workspace you can use `Meta + Shift + C`, if you want to move the application and view special workspace, use `Meta + C`. To just view the special workspace, you can use `Meta + S` and also exit the special workspace if necessary.

13. Free space.

   To move to a free space you can use `Alt + 1` or click on the plus sign at the workspace indicator in the waybar.

14. Floating windows and spaces. 

* In order to switch to floating mode for a particular window, you need to have it in a focused state and by combining `Meta + Shift + E` you can change the mode of the window, as well as you can remove the floating mode for the window.

* In order to float an entire space, you need to use the key combination `Meta + E`, you can also remove the floating mode for the space.

15. Auto gaps:

   This function works in such a way that if only one application is running in the current workspace, the window decorations will be removed and the gaps between the application will be removed, but if you are running or already have more than one application in the workspace, all decorations and gaps will be enabled for the applications.

   <img src="Media/12.png" width="900"/>

   <img src="Media/13.png" width="900"/>


## Plugins that are used:

* Overview - https://github.com/DreamMaoMao/hycov


## Useful links:

* setting gtkgreet <br>
https://www.reddit.com/r/hyprland/comments/13gl7mc/use_hyprland_to_start_gtkgreet/ <br>
https://wiki.archlinux.org/title/Greetd

* configuring bluetooth for battery display <br>
https://askubuntu.com/questions/1117563/check-bluetooth-headphones-battery-status-in-linux

* how to install proprietary drivers for nvidia <br>
https://wiki.hyprland.org/Nvidia/
