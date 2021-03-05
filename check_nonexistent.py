import requests
import json
from main import get_makes, get_payload, get_resource_urls, make_image, get_vifnum
import config

def get_makes(session, base, headers):
    url = base + '/makes/'
    r = session.get(url, headers=headers, timeout=10)
    assert(r.status_code == 200)
    makes = r.json()['data']
    return makes

check_vifnum = True

def test(nonexistent, missing_colors):
    base = 'http://api.evoximages.com/api/v1'
    headers = {'x-api-key': config.api_key}
    session = requests.Session()
    session.headers.update(headers)
    makes = get_makes(session, base, headers)

    vin = '0001346225'
    # vehicle = "2013 Lexus Gx 460"  # F, 350C
    # print(vehicle)
    # payload = get_payload(session, vehicle, makes)
    # payload = {'year': '2015', 'make': 'BMW'}
    payload = {'year': '2012', 'make': 'Cadillac', 'model': 'Escalade Esv'}

    # vifnum check
    if check_vifnum:
        url = base + '/vehicles'
        # payload['model'] = ' '.join(payload['model'])
        print(payload)
        r = requests.get(url, params=payload, headers=headers, timeout=10)
        result = r.json()
        if r.status_code == 200:
            [print(vehicle['vehicle_str']) for vehicle in result['data']]
        else:
            print("NO DATA MATCH")
        exit(0)
    else:
        # image check
        # vifnum = get_vifnum(base, payload, headers, nonexistent)
        # productId = 29
        # productTypeId = 237
        # print("vifnum = {}, productId = {}, productTypeID = {}".format(vifnum, productId, productTypeId))
        # url = base + '/vehicles/' + str(vifnum) + '/products/' + str(productId) + '/' + str(productTypeId)
        # r = requests.get(url, headers=headers, timeout=10)
        # print(json.dumps(r.json(), indent=4))
        # exit(0)
        vifnum, images = get_resource_urls(base, payload, headers, nonexistent, missing_colors)
        if vifnum is not None and images is not None:
            make_image(images[0], vin)


if __name__ == '__main__':
    nonexistent =  open('nonexistent.txt', 'w')
    missing_colors = open('missing_colors.txt', 'w')
    test(nonexistent, missing_colors)
