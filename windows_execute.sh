#!/bin/bash
.\env\Scripts\activate mailers_env
python3 main.py
.\env\Scripts\deactivate mailers_env
