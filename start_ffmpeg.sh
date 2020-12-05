#!/bin/bash
VIDEO_SIZE=864x480
FPS=20

# load module
sudo modprobe v4l2loopback video_nr=20,21

v4l2loopback-ctl set-timeout-image -t 3000 /dev/video20 /home/pi/mmotorhome/res/timeout.png
v4l2loopback-ctl set-timeout-image -t 3000 /dev/video21 /home/pi/mmotorhome/res/timeout.png

ffmpeg -f v4l2 \
       -framerate $FPS \
       -video_size $VIDEO_SIZE \
       -i /dev/video0 \
       -f v4l2 /dev/video20 \
       -f v4l2 /dev/video21 > /dev/null 2>&1

