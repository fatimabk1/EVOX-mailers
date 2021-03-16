#!/bin/bash

source env/bin/activate mailers_env
python3 main.py
source env/bin/deactivate mailers_env
