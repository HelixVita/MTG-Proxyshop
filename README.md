# plugins-dev — FelixVita's development branch for plugins
The code in this branch should be the same as `MrTeferi/MTG-Proxyshop:main` in every way _except_ that it also includes my own Proxyshop plugin folder [FelixVita-Proxyshop-Plugins](https://github.com/HelixVita/FelixVita-Proxyshop-Plugins) as a "git submodule".

## Why?
In general, all proxyshop plugins are required to be in their own git repo. However, since I prefer working with the python version of Proxyshop instead of the EXE version, this requires me to to have a _repo inside a repo_ (my plugin repo inside the MTG-Proxyshop repo). And the best way to achieve this is by using git submodules.

## Instructions
After cloning this repo and switching to this branch, you'll probably notice that the dir `FelixVita-Proxyshop-Plugins` is empty. That's because submodules are not populated by default. In order to populate it you just need to run
```shell
git submodule update --init --recursive
```
