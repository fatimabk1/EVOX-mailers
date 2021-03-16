#!/bin/bash
python3 -m pip install --user --upgrade pip
python3 -m venv mailers_env
source env/bin/activate mailers_env
python3 -m pip install requirements.txt
source env/bin/deactivate mailers_env
