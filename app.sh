#! /bin/bash

APPDIR=$1

source activate oaipy

cd 'run'/${APPDIR}

python app.py
