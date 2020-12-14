#!/bin/bash
SEG_TIME=300 # segment time in sec

/usr/bin/ffmpeg -f v4l2 \
                -i $1 \
                -vb 512k \
                -c:v h264_omx \
                -filter_complex \
                "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:\
                fontcolor=yellow@0.8:\
                text='%{localtime\:%d-%m-%Y %T}:x=5:y=680:fontsize=30'"\
                -f segment \
                -segment_time $SEG_TIME \
                -strftime 1 \
                "/home/pi/motorhome/videos/dashcam_%Y-%m-%d_%H-%M-%S.mp4" 
#> /dev/null 2>&1
