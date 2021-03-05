import csv
import asyncio
from aiohttp import ClientSession, ClientTimeout, TCPConnector, DummyCookieJar
from multiprocessing import Process, Queue, Pipe
import json
import requests
import traceback
import imageio
import beepy
import config

base = 'http://api.evoximages.com/api/v1'
headers = {'x-api-key': config.api_key}


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
        self.code_to_color = {}
        self.color_to_code = {}
        self.resources = None
        self.selected_resource = None


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
        if len(vehicle.list_b) == 0:
            vehicle.vifnum = matches[0]['vifnum']
        else:
            best_match = None
            best_count = 0
            for match in matches:
                match_str = match['vehicle_str'].lower()
                count = 0
                for tok in vehicle.list_b:
                    if tok.lower() in match_str:
                        count += 1
                if count > best_count:
                    best_count = count
                    best_match = match
            if best_count == 0:

                vehicle.vifnum = None
            else:
                vehicle.vifnum = best_match['vifnum']


async def fetch(url, params, session):
    retry = True
    while retry is True: 
        if params is not None:
            async with session.get(url, params=params, headers=headers) as response:
                result = await response.text()
        else:
            async with session.get(url, headers=headers) as response:
                result = await response.text()
        
        # catch 504 Gateway Timeouts
        try:
            result = json.loads(result)
            retry = False
        except:
            print(params)
            if "504" in result.lower():
                print("\tGOT ONE!!!! -- retrying next round")
                retry = True
            else:
                print(result)
                retry = False
    return result


async def bound_fetch(sem, url, params, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, params, session)


async def fetch_all(urls, params, loop):
    tasks = []
    dummy_jar = DummyCookieJar()
    timeout = ClientTimeout(total=600)
    connector = TCPConnector(limit=40)
    sem = asyncio.Semaphore(1000)

    # async with ClientSession(loop=loop, timeout=timeout, cookie_jar=dummy_jar) as session:
    async with ClientSession(loop=loop, connector=connector, timeout=timeout, cookie_jar=dummy_jar) as session:
        if params is None:
            print("NO params")
            for u in urls:
                task = asyncio.ensure_future(bound_fetch(sem, u, None, session))
                tasks.append(task)
        else:
            print("YES params")
            for index, u in enumerate(urls):
                task = asyncio.ensure_future(bound_fetch(sem, u, params[index], session))
                tasks.append(task)
        results = await asyncio.gather(*tasks)
        print("\tresults gathered")
        for r in results:
            assert(r is not None)
        return results


def get_vifnums(vehicles):
    # FETCH ALL
    url = base + '/vehicles'
    url_list = [url for v in vehicles]
    payload_list = [v.payload for v in vehicles]
    loop = asyncio.get_event_loop()
    vifnum_results = loop.run_until_complete(fetch_all(url_list, payload_list, loop))
 
    # handle vehicles with matches
    for i, vehicle in enumerate(vehicles):
        vehicle.vif_result_object = vifnum_results[i]
        # print(vifnum_results[i])
        assert('statusCode' in vifnum_results[i]), print(vehicle.vif_result_object)
        if vifnum_results[i]['statusCode'] == 200:
            handle_vif_match(vehicle)

    # try less specific models until we find a match
    fail_list = [v for v in vehicles if v.vifnum == 0]
    print("\n\n failed vehicles:")
    for v in fail_list:
        assert(v is not None)
        print(v.string)
        print("\t", v.payload)
    print("\n")

    while len(fail_list) != 0:
        # update payload
        for v in fail_list:
            if len(v.list_a) == 0:
                print(v.string)
                print("\t", v.payload)
                print("\t>>>>>>>> CONFIRMED FAILURE")
                v.vifnum = None
                fail_list.remove(v)
            else:
                tok = v.list_a.pop()
                v.list_b.insert(0, tok)
                v.payload['model'] = ' '.join(v.list_a)
        
        # query again
        url_list = [url for v in fail_list]
        payload_list = [v.payload for v in fail_list]
        loop = asyncio.get_event_loop()
        vifnum_results = loop.run_until_complete(fetch_all(url_list, payload_list, loop))

        for i, vehicle in enumerate(fail_list):
            vehicle.vif_result_object = vifnum_results[i]
            assert('statusCode' in vifnum_results[i]), print(vehicle.vif_result_object)
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


def get_colors(vehicles):
    for v in vehicles:
        assert(v is not None)

    color_pool = ["White", "Silver", "Blue", "Black", "Gray"]
    urls = [base + '/vehicles/' + str(v.vifnum) + '/colors' for v in vehicles]
    loop = asyncio.get_event_loop()
    color_results = loop.run_until_complete(fetch_all(urls, None, loop))

    for index, v in enumerate(vehicles):
        colors = color_results[index]['data']['colors']
        for item in colors:
            clr = item['simpletitle']
            if clr in color_pool:
                v.color_to_code[clr] = item['code']
                v.code_to_color[item['code']] = clr
    for v in vehicles:
        assert(v.color_to_code is not None)
        assert(v.code_to_color is not None)
    print("\n\nCOLORS:")
    for v in vehicles:
        print(v.string)
        for clr in v.color_to_code:
            print("\t", clr)
        print("\n")


def get_resource_urls(vehicles):
    for v in vehicles:
        if int(v.payload['year']) < 2007:
            v.productTypeId = '235'
        else:
            v.productTypeId = '237'

    urls = [base + '/vehicles/' + str(v.vifnum) + '/products/29/' + str(v.productTypeId) for v in vehicles]
    loop = asyncio.get_event_loop()
    resource_results = loop.run_until_complete(fetch_all(urls, None, loop))

    print(json.dumps(resource_results[0], indent=4))

    for i, vehicle in enumerate(vehicles):
        if resource_results[i]['status'] != "success":
            print(">>> no stills for : ", vehicle.payload, ", vifnum: ", vehicle.vifnum)
        else:
            vehicle.resources = resource_results[i]['urls']
    
    print("\n\nRESOURCES:")
    for v in vehicles:
        print(v.string)
        for url in v.resources:
            print("\t", url)
        print("\n")        


def select_resources(vehicle):
    print("in select_resource()")
    if vehicle.resources is None:
        vehicle.selected_resource = 'sillhouette.jpg'
        return

    resource_urls =  vehicle.resources
    assert(len(resource_urls) > 0)
    color_to_code = vehicle.color_to_code
    code_to_color = vehicle.code_to_color

    # print("> vehicle: ", vehicle.string)
    # print("> color_to_code: ", vehicle.color_to_code)
    # print("> code_to_color: ", vehicle.code_to_color)
    # print("> vehicle: ", vehicle.string)
    # print("> urls:")
    for url in vehicle.resources:
        print("\t>", url)

    codes = list(color_to_code.values())
    code_start = len(resource_urls[0]) - 4 - len(codes[0])
    code_end = len(resource_urls[0]) - 4

    pos_one_pref = {'Blue': 5, 'Black': 4, 'Gray': 3, 'Silver': 2, 'White': 1 }
    pos_two_pref = {'White': 5, 'Black': 4, 'Gray': 3, 'Blue': 2, 'Silver': 1 }
    pos_three_pref = {'Silver': 5, 'Gray': 4, 'Black': 3, 'White': 2, 'Blue': 1 }
    preferences = [pos_one_pref, pos_two_pref, pos_three_pref]

    pref = preferences[vehicle.position - 1]
    priority = 0
    for resource in resource_urls:
        code = resource[code_start:code_end]
        if code not in code_to_color:
            continue
        color = code_to_color[code]
        if pref[color] > priority:
            priority = pref[color]
            vehicle.selected_resource = resource


def reader(pipe):
    p_in, p_out = pipe
    p_in.close()
    while True:
        img = p_out.recv()
        if img == "DONE":
            break
        else:
            # print(img)
            imageio.imwrite(img[1], img[0], format=".jpg")

def writer(p_in, vehicles):
    for v in vehicles:
        print("\tsending")
        save_path = "images/" + str(v.vin) + ".jpg"
        if v.selected_resource is None:
            v.selected_resource = 'sillhouette.jpg'
            p_in.send([imageio.imread(v.selected_resource, '.jpg'), save_path])
        else:
            p_in.send([imageio.imread(imageio.core.urlopen(v.selected_resource).read(), '.jpg'), save_path])
        # p_in.send(v.vin)
    p_in.send("DONE")


def pipe_make_images(vehicles):
    p_in, p_out = Pipe()
    reader_proc = Process(target=reader, args=((p_in, p_out), ))
    reader_proc.daemon = True
    reader_proc.start()
    p_out.close()
    writer(p_in, vehicles)
    p_in.close()
    reader_proc.join()


def get_makes():
    url = base + '/makes/'
    r = requests.get(url, headers=headers, timeout=10)
    print(r)
    assert(r.status_code == 200)
    makes = r.json()['data']
    return makes


def process():
    with open('data/test_data.csv', 'r') as input:
        reader = csv.DictReader(input)
        vehicles = []
        for row in reader:
            if row["VIN1"] is not "":
                v = Vehicle(row["VIN1"], row["Vehicle1"], 1)
                vehicles.append(v)

            if row["VIN2"] is not "":
                v = Vehicle(row["VIN2"], row["Vehicle2"], 2)
                vehicles.append(v)

            if row["VIN3"] is not "":
                v = Vehicle(row["VIN3"], row["Vehicle3"], 3)
                vehicles.append(v)
        
        for v in vehicles:
            print(v.string)
        print("\n")

        makes = get_makes()
        [get_payload(v, makes) for v in vehicles]  # sets list_a, list_b and payload for each vehicle
        get_vifnums(vehicles)
        for v in vehicles:
            assert(v is not None)
        get_colors(vehicles)
        get_resource_urls(vehicles)
        [select_resources(v) for v in vehicles]
        [print(v.string, ": ", v.selected_resource) for v in vehicles]
        pipe_make_images(vehicles)


if __name__ == "__main__":
    # TODO: get API key from env variable to ensure security
    
    # session = requests.Session()
    # session.headers.update(headers)

    
    print("\n-----------------------------------------------\n")

    try:
        process()
        beepy.beep(sound=5)
    except Exception as e:
        beepy.beep(sound=3)
        traceback.print_exc()
        print(e)
