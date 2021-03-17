import requests
import json
import config


base = 'http://api.evoximages.com/api/v1'
err_vehicle = open('err_vehicle.txt', 'w')
err_resource = open('err_resource.txt', 'w')

if __name__ == '__main__':
    payload = {'year': '2002', 'make': 'Ford', "model": "Escape"}
    results = requests.get(base + '/vehicles', params=payload, headers=config.headers)
    results = results.json()['data']
    vifnum = results[0]['vifnum']

    url = base + '/vehicles/' + str(vifnum) + '/products/29/' + str(235)
    result = requests.get(url, headers=config.headers)
    result = result.json()
    print(json.dumps(result, indent=4))
    assert(result.status_code == 200)
    result = result.json()['data']
    exit(0)

    results = requests.get(base + '/vehicles', params=payload, headers=config.headers)
    print(results.text)
    assert(results.status_code == 200)
    results = results.json()['data']
    for r in results:
        if "silverado" in r['vehicle_str'].lower():
            print(json.dumps(results, indent=4))
    print(payload)
    [print(r['vehicle_str']) for r in results]
