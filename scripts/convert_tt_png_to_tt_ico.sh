#!/usr/bin/env sh
cd `dirname $0`
magick convert "../images/themetrack.png" -define icon:auto-resize=16,48,256 -compress zip "../images/themetrack.ico"

ls -l "../images/themetrack.ico"

