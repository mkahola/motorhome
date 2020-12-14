#!/bin/bash
VIDEO_SIZE=1280x720
FPS=20

#v4l2loopback-ctl set-caps "video/x-raw, format=UYVY, width=1280, height=720" /dev/video20
#v4l2loopback-ctl set-caps "video/x-raw, format=UYVY, width=1280, height=720" /dev/video21
v4l2loopback-ctl set-fps $FPS /dev/video20
v4l2loopback-ctl set-fps $FPS /dev/video21

v4l2loopback-ctl set-timeout-image -t 3000 /dev/video20 /home/pi/mmotorhome/res/timeout.png
v4l2loopback-ctl set-timeout-image -t 3000 /dev/video21 /home/pi/mmotorhome/res/timeout.png

ffmpeg -re \
       -f v4l2 \
       -framerate $FPS \
       -video_size $VIDEO_SIZE \
       -i /dev/video0 \
       -f v4l2 /dev/video20 \
       -framerate $FPS \
       -video_size $VIDEO_SIZE \
       -f v4l2 /dev/video21 \
       -framerate $FPS \
       -video_size $VIDEO_SIZE > /dev/null 2>&1

