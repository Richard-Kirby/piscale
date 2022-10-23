#!/bin/bash
export DISPLAY="unix$DISPLAY"
xhost +si:localuser:root
/usr/bin/python3 /home/kirbypi/piscale/scale_gui.py
