// Compile-time code theming: build.py passes --input target=/content/...typ
#set raw(theme: read("catppuccin.tmTheme", encoding: none))
#include sys.inputs.target
