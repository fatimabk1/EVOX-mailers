#!/bin/bash
python3 -m pip install --user --upgrade pip
python3 -m venv mailers_env
source mailers_env/bin/activate
python3 -m pip install -r requirements.txt
source deactivate mailers_env
