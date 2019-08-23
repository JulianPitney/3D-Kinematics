for /r %%i in (*.yuv) do ffmpeg -f rawvideo -pix_fmt gray -video_size 640x480 -framerate 300 -i %%i -c:v libx265 -crf 10 -preset ultrafast %%~ni.mp4
