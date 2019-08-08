for /r %%i in (*.yuv) do ffmpeg -f rawvideo -pix_fmt gray -video_size 1440x1080 -framerate 46 -i %%i -c:v libx265 -crf 10 -preset ultrafast %%~ni.mp4
