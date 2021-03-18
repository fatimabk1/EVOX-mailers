import requests
import json
import config


base = 'http://api.evoximages.com/api/v1'


def run(resolution: int):
    v = {'year': '2012', 'make': 'Honda', "model": "CR-V"}

    year = int(v['year'])

    results = requests.get(base + '/vehicles', params=v, headers=config.headers)
    result = results.json()['data'][0]
    # print(json.dumps(result, indent=4))


    # only angle 001 available
    if year < 2007:
        # v['productTypeId'] = 235
        if resolution == 320:
            v['productTypeId'] = 232
        elif resolution == 480:
            v['productTypeId'] = 235
        elif resolution == 640:
            v['productTypeId'] = 238
        elif resolution == 1280:
            v['productTypeId'] = 244
        elif resolution == 2400:
            v['productTypeId'] = 247
    # angle 032
    else:
        # v['productTypeId'] = 237
        if resolution == 320:
            v['productTypeId'] = 234
        elif resolution == 480:
            v['productTypeId'] = 237
        elif resolution == 640:
            v['productTypeId'] = 242
        elif resolution == 1280:
            v['productTypeId'] = 246
        elif resolution == 2400:
            v['productTypeId'] = 251

    url = base + '/vehicles/' + str(result['vifnum']) + '/products/29/' + str( v['productTypeId'])
    result = requests.get(url, headers=config.headers)
    result = result.json()
    print(json.dumps(result, indent=4))
    # assert(result.status_code == 200)
    # result = result.json()['data']
    return
    # exit(0)

    results = requests.get(base + '/vehicles', params=payload, headers=config.headers)
    print(results.text)
    assert(results.status_code == 200)
    results = results.json()['data']
    for r in results:
        if "silverado" in r['vehicle_str'].lower():
            print(json.dumps(results, indent=4))
    print(payload)
    [print(r['vehicle_str']) for r in results]

if __name__ == '__main__':
    resolution = 2400
    run(resolution)
