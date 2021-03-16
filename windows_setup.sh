 #!/bin/bash

py -m pip install --upgrade pip
py -m venv mailers_env
.\mailers_env\Scripts\activate
python3 -m pip install requirements.txt
.\mailers_env\Scripts\deactivate
