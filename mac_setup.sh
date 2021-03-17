#!/bin/bash
python3 -m pip install --user --upgrade pip
pip install virtualenvwrapper
/bin/bash -c '/usr/local/bin/virtualenvwrapper.sh'
/bin/bash -c '/usr/local/bin/virtualenvwrapper.sh mailers_env'
/bin/bash -c 'workon mailers_env'
python3 -m pip install -r requirements.txt
/bin/bash -c 'deactivate'
