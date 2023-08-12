#!/bin/bash
export DISPLAY="unix$DISPLAY"
xhost +si:localuser:root
/usr/bin/python3 /home/kirbypi/piscaleV2/piscale/scale_gui.py
