for /r %%i in (*.yuv) do ffmpeg -f rawvideo -pix_fmt gray -video_size 720x540 -framerate 56 -i %%i -c:v libx265 -crf 10 -preset ultrafast %%~ni.mp4
