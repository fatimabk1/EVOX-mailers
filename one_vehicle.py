import csv
import asyncio
from datetime import datetime
from multiprocessing import Process, Pipe
import requests
import traceback
import time
import json
import imageio
import beepy
import config
import clientFetch
import output_check
import animation
from alive_progress import alive_bar
import main

base = 'http://api.evoximages.com/api/v1'
headers = {'x-api-key': config.api_key}
err_vehicle = open('err_vehicle.txt', 'w')
err_resource = open('err_resource.txt', 'w')

if __name__ == '__main__':
    # r = requests.get('http://api.evoximages.com/api/v1/vehicles/216/colors', headers=headers)
    # print(json.dumps(r.json(), indent=4))
    # exit(0)

    payload = {'year': '2002', 'make': 'Hello'}
    results = requests.get(base + '/vehicles', params=payload, headers=headers)
    print(results.text)
    assert(results.status_code == 200)
    results = results.json()['data']
    for r in results:
        if "silverado" in r['vehicle_str'].lower():
            print(json.dumps(results, indent=4))
    print(payload)
    [print(r['vehicle_str']) for r in results]
