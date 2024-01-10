# Hyprland Dotfiles

> Этот репозиторий содержит dotfiles для Hyprland, настраиваемой среды рабочего стола, созданной для дистрибутива на основе Arch Linux. Эти точечные файлы предназначены для улучшения внешнего вида и функциональности Hyprland.

## Установка

Чтобы использовать эти точечные файлы, выполните следующие действия:

1. Клонируем репозиторий:

~~~
git clone https://gitlab.com/BA_usr/dotfiles-for-hyperland.git
~~~

2. Перейдите в клонированный каталог:

~~~
cd dotfiles-for-hyperland
~~~

3. Установите необходимые пакеты:

~~~
yay -S ttf-twemoji waybar kitty ttf-jetbrains-mono-nerd pavucontrol jq nvidia-settings libnotify dunst slurp grim wl-clipboard xdg-desktop-portal-hyprland libcanberra wireless_tools pamixer xdg-user-dirs blueberry wlrobs-hg hyprshade greetd greetd-gtkgreet cage
~~~

4. Настройте dotfiles в соответствии с вашими предпочтениями.

## Функциональность

##### Файлы точек Hyprland предлагают следующие функции:

1. Захват экрана для скриншота
- Сделайте снимок экрана, нажав кнопку `Print Screen`. Это позволит вам выбрать конкретную область, чтобы сделать снимок экрана.

2. Меню обзора приложений
- Откройте меню обзора приложений, нажав `Alt + R` или щелкнув по логотипу Arch Linux на панели waybar.
 <img src="Media/2.png" alt="Меню обзора приложений" width="900"/>

3. Управление обоями
- Измените обои, нажав , `Alt + W` чтобы открыть меню обоев. Нажатие `Meta + Shift + W` установит случайные обои из коллекции.
 <img src="Media/3.png" width="900"/>

4. Меню быстрых настроек. Для вызова меню быстрых настроек нажмите сочитание клавиш `Alt + с`. В данном меню есть виджет:
- WiFi - для подключения к сети и отображения сети;
- Bluetooth - для подключения и отображения включен он или нет;
- Night Color - изменение цветовой гаммы с целью убрать синий свет экана;
- виджет "Не беспокоить" - отключение или включение уведомлений;
- индикатор зарядки последнего подключенного Bluetooth устройства
- виджет отображающий погоду;
- слайдер для переключения выходящего и входящего звука.
 <img src="Media/6.png" width="900"/>

- MPRIS плеер работающий на playerctl
<img src="Media/7.png"/>

5. Индикатор звука. Данный индикатор отображает звук при изменении его через: 
- сочетание клавиш `Fn + F10` и `Fn + F11`;
- изменение через меню быстрых настроек в ручном режиме.
   Данный индикатор работает в фоне и появляется только тогда, когда он замечает изменения в уровне звука.

<img src="Media/4.png" width="900"/>

> Индикатор звука поломан, из-за ошибки с функцией `eww update` для `defvar`, если вы уверены что у вас будет работать правильно eww, то можете из ветки `V1` извлечь папку для индикатора и поместить её в `~/.config/eww`

6. Bluetooth меню. Данное меню вызывается из быстрых настроек по нажатию на кнопку Bluetooth.

<img src="Media/5.png" width="900"/>

7. WiFi меню. Данное меню вызывается из быстрых настроек по нажатию на кнопку WiFi.

<img src="Media/8.png" width="900"/>

8. Используя комбинацию клавиш `ALT + Tab`, вы сможете переключать фокус на приложения находящиеся в текущем workspace.

9. Overview. 

* Используя комбинацию клавиш `Meta + Tab`, вы сможете вызвать Overview и просмотреть все приложения на всех workspaces. Переключить фокус в overview вы можете через комбинации клавиш `ALT + Tab`,`Meta + Arrows` и что бы переместиться к свокусированному приложению вы можете нажав `левой кнопки мыши` или нажав еще раз `Meta + Tab`.

![Overview](Media/1.mp4)

10. Цент уведомлений.

<img src="Media/9.png" width="900"/>

<img src="Media/10.png" width="900"/>

11. Bluetooth индикатор. Индикатор отображающий есть ли подключенное устройство и если оно подключенно и у вас включена настройка для отображения батареи, то вы сможете увидить объем батареи. Если к вашему пк подключено больше чем одно Bluetooth устройсво, то иконка изменит свой статус на панели и перестанет отображать объем батареии, но что бы по смотреть объем батареи всех устройсв, вы можете нажать на индикатор и появится окно отображающие все устройсва с их статусами.

Ниже пример с одним подключенным устройством:

<img src="Media/11.png" width="900"/>

12. Special workspace.

* Для перемещения приложения в special workspace можно нажав комбинацию `Meta + Shift + C`, если вы хотите переместить приложение и просматривать special workspace, то используйте `Meta + C`. Для того что бы просто просмотреть special workspace, вы можете использовать `Meta + S` и так же если необходимо выйти из этого пространства.

13. Свободное пространство.

* Для перехода в свободное пространство вы можете использовать `Alt + 1` или нажав на значек плюса у индикатора workspace в waybar.

14. Плавующие окна и пространства. 

* Для того что бы переключить в плавующий режим определенное окно, вам нужно что бы оно было сфокусированное и по сочитанию `Meta + Shift + E` вы сможете изменить режим окна, так же можно и убрать плавующий режим для окна.

* Для того что бы переключить в плавующий режим целое пространство, вам нужно использовать сочетание клавиш `Meta + E`, так же можно и убрать плавующий режим.


## Плагины которые используются:

* Overview - https://github.com/DreamMaoMao/hycov


## Полезные ссылки:

* настройка gtkgreet <br>
https://www.reddit.com/r/hyprland/comments/13gl7mc/use_hyprland_to_start_gtkgreet/ https://wiki.archlinux.org/title/Greetd

* настройка bluetooth для отображения батареи <br>
https://askubuntu.com/questions/1117563/check-bluetooth-headphones-battery-status-in-linux

* как правильно установить proprietary драйвера для nvidea <br>
https://wiki.hyprland.org/Nvidia/