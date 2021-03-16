 #!/bin/bash

py -m pip install --upgrade pip
py -m venv mailers_env
.\env\Scripts\activate mailers_env
python3 -m pip install requirements.txt
.\env\Scripts\deactivate mailers_env
