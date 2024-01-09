#!/bin/bash

# Replace /path/to/venv with the path to your virtual environment
source dc_env/bin/activate

# Start bot.py in the background
nohup python3 bot.py >> imagenationbot.log 2>&1 &

# Start scheduler.py in the background
nohup python3 scheduler.py >> imagenationbot.log 2>&1 &
