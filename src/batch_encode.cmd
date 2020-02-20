for /r %%i in (*.yuv) do ffmpeg -n -f rawvideo -pix_fmt gray -video_size 1440x1080 -framerate 56 -i %%i -c:v libx265 -crf 10 -preset ultrafast %%~ni.mp4
for /r %%i in (*.yuv) do del /f %%~ni.yuv
