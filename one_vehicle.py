import requests
import json


base = 'http://api.evoximages.com/api/v1'
err_vehicle = open('err_vehicle.txt', 'w')
err_resource = open('err_resource.txt', 'w')

if __name__ == '__main__':
    payload = {'year': '2002', 'make': 'Hello'}
    results = requests.get(base + '/vehicles', params=payload, headers=config.headers)
    print(results.text)
    assert(results.status_code == 200)
    results = results.json()['data']
    for r in results:
        if "silverado" in r['vehicle_str'].lower():
            print(json.dumps(results, indent=4))
    print(payload)
    [print(r['vehicle_str']) for r in results]
