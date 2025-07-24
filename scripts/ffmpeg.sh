#!/bin/bash
# Script para converter YUV para MP4 e empacotar com MP4Box

RES="352x288"              # Altere para a resolução do seu vídeo
YUVFILE="input.yuv"
MP4OUT="output.mp4"
MP4FINAL="final.mp4"

ffmpeg -s $RES -pix_fmt yuv420p -i $YUVFILE -c:v libx264 -preset veryfast -crf 24 $MP4OUT
MP4Box -add $MP4OUT -new $MP4FINAL

echo "Arquivo convertido e empacotado: $MP4FINAL"
