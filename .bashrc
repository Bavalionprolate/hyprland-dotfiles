#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'

emoji=( 🥝 🍀 🍘 🍚 🍙 🐸 🌈 🌑 🌕 🌙 🌚 🌝 🍛 🍞 🍟 🍡 🍢 🍣 🍥 💔 💜 🥑 🥦 🥥 🥪 🥒 🥓 🦑 🧀)

# функция для случайного выбора эмодзи
choose_emoji() {
  local random_index=$((RANDOM % ${#emoji[@]}))
  echo "${emoji[random_index]}"
}

# используем случайный выбор эмодзи в PS1
PS1="\$(choose_emoji) \W \$ "
