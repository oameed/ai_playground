#! /bin/bash

APPDIR=$1

source activate aipy

cd 'run'/${APPDIR}

python app.py
