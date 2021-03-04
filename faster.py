import csv
import asyncio
from socket import timeout
from aiohttp import ClientSession, ClientTimeout, TCPConnector, DummyCookieJar
import requests
import json
import traceback
import imageio
import random
from datetime import datetime, timedelta
import beepy
from main import get_makes
import config


class Vehicle:
    def __init__(self, vin, string, position):
        self.position = position
        self.vin = vin
        self.string = string
        self.payload = None
        self.list_a = None
        self.list_b = None
        self.vif_result_object = None
        self.vifnum = 0
        self.productTypeId = None
        self.code_to_color = None
        self.color_to_code = None
        self.resources = None
        self.selected_resource = None

def log():
    return datetime.now()


def delta(msg, start):
    curr = datetime.now()
    print(msg + "∆: ", curr - start)


def get_payload(vehicle, makes):   
    string = vehicle.string
    tokens = str.split(string)
    year = tokens[0]

    # convert make excel->database
    make = None
    index = 1
    m = tokens[index]
    if m == "Mercedes_Benz":
        make = "Mercedes-Benz"
    elif m == "Rolls_Rocye":
        make = "Rolls-Royce"
    elif m == "Land":
        make = "Land Rover"
        index += 1
    elif m == "Aston":
        make = "Aston Martin"
        index += 1
    elif m == "Alfa":
        make = "Alfa Romero"
        index += 1
    elif m == "Range":
        make = "Land Rover"
        index +=1
    elif m == "Bmw":
        make = "BMW"
    else:
        in_list = m.lower() in (mk.lower() for mk in makes)
        if in_list:
            make = m
        else:
            print("Invalid Make: vehicle = {}, m = {}".format(vehicle, m))
            print("ALL MAKES:")
            for mk in makes:
                print(mk)

    model_toks = tokens[index + 1:]

    # print("model_toks: ", model_toks)

    # delete and reorder tokens
    if make.lower() == "ram" and model_toks[0].lower() == "ram":
        del model_toks[0]
 
    if len(model_toks) == 2:
        if model_toks[0].lower() == "cooper" and model_toks[1].lower() == "countryman":
            del model_toks[0]
        elif "hd" in model_toks[1].lower() and len(model_toks[1]) > 2:
            letters = len(model_toks[1])
            model_toks[1] = model_toks[1][:letters - 2]
            tok = "HD"
            model_toks.append(tok)
        elif model_toks[0].lower() == "a4":
            del model_toks[1]
        elif int(year) > 2010 and model_toks[0].lower() == "ram" and make.lower() == "dodge":
            make = "RAM"
            del model_toks[0]
        elif model_toks[0].lower() == "accord" and model_toks[1].lower() == "crosstour":
            model_toks[1] = "EX"
        elif model_toks[0].lower() == "expedition" and model_toks[1].lower() == "el":
            del model_toks[1]
        elif model_toks[0].lower() == "yukon" and model_toks[1].lower() == "xl":
            del model_toks[1]
        elif make.lower() == "infiniti" and "g" == model_toks[0].lower()[0]:
            number = model_toks[0][1:]
            model_toks[0] = "G"
            model_toks.append(number)
            # del model_toks[1]
            # model_toks --> ['G Sedan', '37']

    elif len(model_toks) == 3:
        if model_toks[0].lower() == "silverado":
            classic = model_toks[2]
            number = model_toks[1]
            model_toks[1] = classic 
            model_toks[2] = number 
        elif model_toks[2].lower() == "coupe":
            model_toks[2] = "Coupe"   
        elif model_toks[1].lower() == "super" and model_toks[2].lower() == "duty":
            del model_toks[2]
            model_toks[1] = "SD"
        elif model_toks[0].lower() == "sierra" and model_toks[2].lower() == "cc":
            del model_toks[2]

    model = ""
    for index, tok in enumerate(model_toks):
        if tok.lower() == "is":
            model_toks[index] = "IS"
        elif tok.lower() == "rx":
            model_toks[index] = "RX"
        elif tok.lower() == "gx":
            print("found gx")
            model_toks[index] = "GX"
        elif tok.lower() == "es":
            model_toks[index] = "ES"
        elif tok.lower() == "gtc":
            model_toks[index] = "GTC"
        # elif tok.lower() == "pickup":
        #     continue
        elif "hd" in tok.lower():
            strlen = len(tok)
            tok = tok[:strlen - 2]
            # if make.lower() == "gmc":
            tok += "HD"  # Sierra accepts HD
        # else:
        #     continue
        
    # print("model = ", model_toks)
    payload = {'year': year,
               'make': make,
               'model': ' '.join(model_toks)}
    # print(payload)
    vehicle.payload = payload
    vehicle.list_a = model_toks
    vehicle.list_b = []


def handle_vif_match(vehicle):
    matches = vehicle.vif_result_object['data']
    if len(matches) == 1:
        vehicle.vifnum = matches[0]['vifnum']
    else:
        for match in matches:
            found = True
            match_str = match['vehicle_str'].lower()
            for tok in vehicle.list_b:
                if tok.lower() not in match_str:
                    found = False
            if found is True:
                vehicle.vifnum = match['vifnum']
                return
        vehicle.vifnum = matches[0]['vifnum']



async def fetch(url, params, headers, session):
    if params is not None:
        async with session.get(url, params=params, headers=headers) as response:
            # data =  await response.read()
            # return json.loads(data)
            # return await response.body.decode('utf-8')
            return await response.text()

    else:
        async with session.get(url, headers=headers) as response:
            return await response.text()


async def fetch_all(urls, params, headers, loop):
    tasks = []
    timeout = ClientTimeout(total=600)
    connector = TCPConnector(limit=40)
    dummy_jar = DummyCookieJar()
    async with ClientSession(loop=loop, connector=connector, timeout=timeout, cookie_jar=dummy_jar) as session:
        if params is None:
            print("NO params")
            for u in urls:
                task = asyncio.ensure_future(fetch(u, headers, session))
                tasks.append(task)
        else:
            print("YES params")
            for index, u in enumerate(urls):
                task = asyncio.ensure_future(fetch(u, params[index], headers, session))
                tasks.append(task)
        results = await asyncio.gather(*tasks)
        print("\tresults gathered")
        return results

async def test(headers):
    url = base + '/vehicles'
    payload = {'year': '2013', 'make': 'Lexus', 'model': 'GX'}
    print("fetch() with response.read()")
    async with ClientSession() as session:
        return await fetch(url, payload, headers, session)


def get_vifnums(base, headers, vehicles):
    # FETCH ALL
    url = base + '/vehicles'
    url_list = [url for v in vehicles]
    payload_list = [v.payload for v in vehicles]
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(fetch_all(url_list, payload_list, headers, loop))
    vifnum_results = [json.loads(r) for r in results]
 
    for i, vehicle in enumerate(vehicles):
        vehicle.vif_result_object = vifnum_results[i]
        # print(json.dumps(vifnum_results[i].json(), indent=4))
        if vifnum_results[i]['statusCode'] == 200:
            handle_vif_match(vehicle)

    # try less specific versions of vehicle until we find a match
    fail_list = [v for v in vehicles if v.vifnum == 0]
    print("\n\n failed vehicles:")
    for v in fail_list:
        print(v.string)
        print("\t", v.payload)
    print("\n")

    while len(fail_list) != 0:
        # update payload
        for v in fail_list:
            if len(v.list_a) == 0:
                vehicle.vifnum = None
                fail_list.remove(vehicle)
            else:
                tok = v.list_a.pop()
                v.list_b.insert(0, tok)
                v.payload['model'] = ' '.join(v.list_a)
        
        # query again
        url_list = [url for v in fail_list]
        payload_list = [v.payload for v in fail_list]
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(fetch_all(url_list, payload_list, headers, loop))
        vifnum_results = [json.loads(r) for r in results]


        for i, vehicle in enumerate(fail_list):
            vehicle.vif_result_object = vifnum_results[i]
            if vifnum_results[i]['statusCode'] == 200:
                handle_vif_match(vehicle)
        fail_list = [v for v in vehicles if v.vifnum == 0]

        print("\n\n failed vehicles:")
        for v in fail_list:
            print(v.string)
            print("\t", v.payload)
        print("\n")
    
    for v in vehicles:
        assert(v.vifnum != 0)
    print("\nsuccessful vifnum extraction ~")
    exit(0)


def get_colors(base, vehicles):
    color_pool = ["White", "Silver", "Blue", "Black", "Gray"]
    urls = [base + '/vehicles/' + str(v.vifnum) + '/colors' for v in vehicles]
    rs = (grequests.get(u, headers=headers) for u in urls)
    vifnum_results = grequests.map(rs)

    for i, vehicle in enumerate(vehicles):
        colors = vifnum_results[i]['data']['colors']
        for item in colors:
            clr = item['simpletitle']
            if clr in color_pool:
                vehicle.color_to_code[clr] = item['code']
                vehicle.code_to_color[item['code']] = clr


def get_resource_urls(base, vehicles):
    for v in vehicles:
        if int(v.payload['year']) < 2007:
            v.productTypeId = '235'
        else:
            v.productTypeId = '237'

    urls = [base + '/vehicles/' + str(v.vifnum) + '/products/29/' + str(v.productTypeId) for v in vehicles]
    rs = (grequests.get(u, headers=headers) for u in urls)
    resource_results = grequests.map(rs)

    for i, vehicle in enumerate(vehicles):
        if resource_results[i].status_code != 200:
            print(">>> no stills for : ", vehicle.payload)
        else:
            vehicle.resources = resource_results[i].json()['urls']


def select_resources(vehicle):
    if vehicle.resources is None:
        vehicle.selected_resource = 'sillhouette.jpg'
        return

    resource_urls =  vehicle.resources
    color_to_code = vehicle.color_to_code
    code_to_color = vehicle.code_to_color
    

    main_count = 0
    general_count = 0
    possible_images = {}
    images = [None, None, None]

    codes = list(color_to_code.values())
    code_start = len(resource_urls[0]) - 4 - len(codes[0])
    code_end = len(resource_urls[0]) - 4


    pos_one_pref = {'Blue': 5, 'Black': 4, 'Gray': 3, 'Silver': 2, 'White': 1 }
    pos_two_pref = {'White': 5, 'Black': 4, 'Gray': 3, 'Blue': 2, 'Silver': 1 }
    pos_three_pref = {'Silver': 5, 'Gray': 4, 'Black': 3, 'White': 2, 'Silver': 1 }
    preferences = [pos_one_pref, pos_two_pref, pos_three_pref]

    pref = preferences[vehicle.position - 1]
    priority = 0

    for resource in resource_urls:
        code = resource[code_start:code_end]
        color = code_to_color[code]
        if pref[color] > priority:
            priority = pref[color]
            vehicle.selected_resource = resource

def make_image(vehicle):
    save_path = "images/" + str(vehicle.vin) + ".jpg"
    print("vehicle.resource: " + vehicle.resource)
    img_in = imageio.imread(imageio.core.urlopen(vehicle.resource).read(), '.jpg')
    img = imageio.imwrite(save_path, img_in, format=".jpg")


def get_makes(base, headers):
    url = base + '/makes/'
    t = log()
    r = requests.get(url, headers=headers, timeout=10)
    delta("\tdb query makes", t)
    assert(r.status_code == 200)
    makes = r.json()['data']
    return makes



def process(base, headers):
    with open('data.csv', 'r') as input:
        reader = csv.DictReader(input)
        vehicles = []
        for row in reader:
            if row["VIN1"] is not None:
                v = Vehicle(row["VIN1"], row["Vehicle1"], 1)
                vehicles.append(v)
            elif row["VIN2"] is not None:
                v = Vehicle(row["VIN2"], row["Vehicle2"], 2)
                vehicles.append(v)
            elif row["VIN3"] is not None:
                v = Vehicle(row["VIN3"], row["Vehicle3"], 3)
                vehicles.append(v)

        makes = get_makes(base, headers)
        [get_payload(v, makes) for v in vehicles]  # sets list_a, list_b and payload for each vehicle
        # print("\n\n\n vehicle saved payloads")
        # [print(v.payload) for v in vehicles]
        get_vifnums(base, headers, vehicles)
        get_colors(base, vehicles)
        get_resource_urls(base, vehicles)
        select_resources(base, vehicles)
        map(make_image, vehicles)


if __name__ == "__main__":
    # TODO: get API key from env variable to ensure security
    base = 'http://api.evoximages.com/api/v1'
    headers = {'x-api-key': config.api_key}
    # session = requests.Session()
    # session.headers.update(headers)

    
    print("\n-----------------------------------------------\n")

    try:
        process(base, headers)
        beepy.beep(sound=5)
    except Exception as e:
        beepy.beep(sound=3)
        traceback.print_exc()
        print(e)
