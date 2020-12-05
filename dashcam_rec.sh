#!/bin/bash
VIDEO_SIZE=864x480
FPS=20

# set fps
v4l2loopback-ctl set-fps $FPS $1

ffmpeg -f v4l2 \
       -framerate $FPS \
       -video_size $VIDEO_SIZE \
       -i $1 \
       -vb 1M \
       -filter_complex \
       "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:\
       fontcolor=yellow@0.8:\
       text='%{localtime\:%d-%m-%Y %T}:x=5:y=450:fontsize=24'"\
       -f segment \
       -segment_time 300 \
       -strftime 1 \
       "/home/pi/motorhome/videos/dashcam_%Y-%m-%d_%H-%M-%S.avi"
#       -f /dev/video21 > /dev/null 2>&1

