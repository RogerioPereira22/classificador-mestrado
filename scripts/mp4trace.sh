#!/bin/bash
# Script para gerar arquivo trace do vídeo empacotado

MP4="final.mp4"
TRACE="trace.txt"

# Versão mais comum para gerar trace offline (remova -s se não usa servidor)
mp4trace -f $MP4 > $TRACE

echo "Trace gerado em: $TRACE"
