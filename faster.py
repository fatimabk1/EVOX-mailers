import csv
import asyncio
from main import log, delta
from datetime import datetime
# from aiohttp import ClientSession, ClientTimeout, TCPConnector, DummyCookieJar
from multiprocessing import Process, Pipe
import json
import requests
import traceback
import time
import imageio
import beepy
import config
import clientFetch
# import pypeln as pl

base = 'http://api.evoximages.com/api/v1'
headers = {'x-api-key': config.api_key}
err504 = open('504_errors.txt', 'w')
err1040 = open('1040_errors.txt', 'w')


class Vehicle:
    def __init__(self, vin, string, position):
        self.position = position
        self.vin = vin
        self.string = string
        self.payload = None
        self.model_toks = None
        self.list_a = None
        self.list_b = None
        self.vif_result_object = None
        self.vifnum = 0  # set to None if no matching vehicle in database
        self.productTypeId = None
        self.code_to_color = {}
        self.color_to_code = {}
        self.resources = None
        self.selected_resource = None
    
    def print(self):
        print("<pos={}, payload={}, vifnum={}, string={}".format(self.position, self.payload, self.vifnum, self.string),
              "\tmodel_toks={}, code_dict={}, color_dict={}>".format(self.model_toks, self.code_to_color, self.color_to_code))


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
        # elif model_toks[2].lower() == "coupe":
        #     model_toks[2] = "Coupe"   
        elif model_toks[1].lower() == "super" and model_toks[2].lower() == "duty":
            del model_toks[2]
            model_toks[1] = "SD"
        elif model_toks[0].lower() == "sierra" and model_toks[2].lower() == "cc":
            del model_toks[2]

    model = ""
    for index, tok in enumerate(model_toks):
        # if tok.lower() == "is":
        #     model_toks[index] = "IS"
        # elif tok.lower() == "rx":
        #     model_toks[index] = "RX"
        # elif tok.lower() == "gx":
        #     model_toks[index] = "GX"
        # elif tok.lower() == "es":
        #     model_toks[index] = "ES"
        # elif tok.lower() == "gtc":
        #     model_toks[index] = "GTC"
        # elif tok.lower() == "pickup":
        #     continue
        if "hd" in tok.lower():
            strlen = len(tok)
            tok = tok[:strlen - 2]
            # if make.lower() == "gmc":
            tok += "HD"  # Sierra accepts HD
        # else:
        #     continue
        
    # print("model = ", model_toks)
    payload = {'year': year,
               'make': make}
            #    'model': ' '.join(model_toks)}
    # print(payload)
    vehicle.payload = payload
    # vehicle.list_a = model_toks
    # vehicle.list_b = []
    vehicle.model_toks = model_toks


def handle_vif_match(vehicle):
    matches = vehicle.vif_result_object['data']
    # if len(matches) == 1:
    #     vehicle.vifnum = matches[0]['vifnum']
    # else:
    #     if len(vehicle.list_b) == 0:
    #         vehicle.vifnum = matches[0]['vifnum']
    #     else:
    best_match = None
    best_count = 0
    for match in matches:
        match_str = match['vehicle_str'].lower()
        count = 0
        # for tok in vehicle.list_b:
        for tok in vehicle.model_toks:
            if tok.lower() in match_str:
                count += 1
        if count > best_count:
            best_count = count
            best_match = match
    if best_count == 0:
        vehicle.vifnum = None
    else:
        vehicle.vifnum = best_match['vifnum']


def get_vifnums(vehicles):
    # fetch all
    url = base + '/vehicles'
    fetches = [[url, v.payload] for v in vehicles]
    loop = asyncio.get_event_loop()
    vifnum_results = loop.run_until_complete(clientFetch.fetch_all(fetches, loop))
 
    # handle vehicles with matches
    for i, vehicle in enumerate(vehicles):
        vehicle.vif_result_object = vifnum_results[i]
        assert('statusCode' in vifnum_results[i]), print(vifnum_results[i])
        if vifnum_results[i]['statusCode'] == 200:
            handle_vif_match(vehicle)

    miss_list = [v for v in vehicles if v.vifnum == 0]
    print("len(miss_list) = ", len(miss_list))
    for v in miss_list:
        print(v.string, " | ", v.payload)
        print("\t>>>>> Confirmed vehicle not in database")
        v.vifnum = None

    # confirm that all vehicles have been handled
    for v in vehicles:
        assert(v.vifnum != 0)
    print("\n>>>>> Sucessfully pulled all vifnums! <<<<<\n")
    beepy.beep(sound=1)

    # START HERE >>>
    # 1. Check for vehicle_str in cache  # SKIP
    # 2. Pull {year, make} & loop through vehicle_strings for best match w/model tokens list
    # 3. Add {(year, make) --> data_list} to cache lookup  # SKIP
    # 4. Add caching {vehicle_string --> vifnum}  # SKIP

    # try less specific models until we find a match
    # while True:
    #     miss_list = [v for v in vehicles if v.vifnum == 0]
    #     for v in miss_list:
    #         if len(v.list_a) == 0:
    #             print("\t", v.payload)
    #             print("\t>>>>>>>> CONFIRMED FAILURE")
    #             v.vifnum = None
    #             miss_list.remove(v)
    #         else:
    #             tok = v.list_a.pop()
    #             v.list_b.insert(0, tok)
    #             v.payload['model'] = ' '.join(v.list_a)

    #     if len(miss_list) == 0:
    #         break

    #     # query again
    #     fetches = [[url, v.payload] for v in miss_list]
    #     print("len(miss_list): ", len(miss_list))
    #     print("# fetches: ", len(fetches))
    #     loop = asyncio.get_event_loop()
    #     print("trying again with {} vehicles".format(len(miss_list)))
    #     vifnum_results = loop.run_until_complete(clientFetch.fetch_all(fetches, loop))
    #     assert(len(vifnum_results) == len(miss_list))

    #     # handle vehicles with matches
    #     for i, vehicle in enumerate(miss_list):
    #         vehicle.vif_result_object = vifnum_results[i]
    #         assert('statusCode' in vifnum_results[i]), print("vifnum result: [{}]".format(vifnum_results[i]))
    #         if vifnum_results[i]['statusCode'] == 200:
    #             handle_vif_match(vehicle)


def get_colors(vehicles):
    for v in vehicles:
        assert(v is not None)

    # urls = [base + '/vehicles/' + str(v.vifnum) + '/colors' for v in vehicles]
    fetches = [[base + '/vehicles/' + str(v.vifnum) + '/colors', None]
                for v in vehicles
                if v.vifnum is not None]
    loop = asyncio.get_event_loop()
    color_results = loop.run_until_complete(clientFetch.fetch_all(fetches, loop))

    # START >>>> NONE VIFNUMS, fetch colors enumerate vehicles mismatch
    index = 0
    for v in vehicles:
        if v.vifnum is None:
            continue
        colors = color_results[index]['data']['colors']
        print("Colors:", v.string)
        [print("\t", clr['simpletitle'], clr['code']) for clr in colors]
        for item in colors:
            clr = item['simpletitle']
            # TODO: remove check for colors in color_pool, collect all
            v.color_to_code[clr] = item['code']
            v.code_to_color[item['code']] = clr
        index += 1
        print("\n ---------------------------")
    for v in vehicles:
        if v.vifnum is None:
            continue
        assert(len(v.color_to_code) != 0), v.print()
        assert(len(v.code_to_color) != 0), v.print()
    print("\n>>>>> Sucessfully pulled all colors! <<<<<\n")
    beepy.beep(sound=1)


def get_resource_urls(vehicles):
    for v in vehicles:
        if int(v.payload['year']) < 2007:
            v.productTypeId = '235'
        else:
            v.productTypeId = '237'

    fetches = [[base + '/vehicles/' + str(v.vifnum) + '/products/29/' + str(v.productTypeId), None] 
                for v in vehicles
                if v.vifnum is not None]
    loop = asyncio.get_event_loop()
    resource_results = loop.run_until_complete(clientFetch.fetch_all(fetches, loop))

    index = 0
    for vehicle in vehicles:
        if vehicle.vifnum is None:
            continue
        else:
            if resource_results[index]['status'] != "success":
                print(">>> no stills for : ", vehicle.payload, ", vifnum: ", vehicle.vifnum)
            else:
                vehicle.resources = resource_results[index]['urls']
            index += 1

    print("\n\nRESOURCES:")
    for v in vehicles:
        print(v.string)
        if v.resources is not None:
            for url in v.resources:
                print("\t", url)
        print("\n")
    print("\n>>>>> Sucessfully pulled all resources! <<<<<\n")
    beepy.beep(sound=1)


def select_resources(vehicle):
    if vehicle.resources is None:
        return

    resource_urls =  vehicle.resources
    assert(len(resource_urls) > 0)
    color_to_code = vehicle.color_to_code
    code_to_color = vehicle.code_to_color

    # print("> vehicle: ", vehicle.string)
    # print("> color_to_code: ", vehicle.color_to_code)
    # print("> code_to_color: ", vehicle.code_to_color)
    print("> vehicle: ", vehicle.string)
    # print("> urls:")
    for url in vehicle.resources:
        print("\t>", url)

    codes = list(color_to_code.values())
    print("codes: ", codes)
    code_start = len(resource_urls[0]) - 4 - len(codes[0])
    code_end = len(resource_urls[0]) - 4

    pos_one_pref = {'Blue': 5, 'Black': 4, 'Gray': 3, 'Silver': 2, 'White': 1 }
    pos_two_pref = {'White': 5, 'Black': 4, 'Gray': 3, 'Blue': 2, 'Silver': 1 }
    pos_three_pref = {'Silver': 5, 'Gray': 4, 'Black': 3, 'White': 2, 'Blue': 1 }
    preferences = [pos_one_pref, pos_two_pref, pos_three_pref]

    # START >>>>
    # TODO: situation where none of preferred colors available -- random color or silhouette image?
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
    print("\n>>>>> Sucessfully created all images! <<<<<\n")
    beepy.beep(sound=1)


def get_makes():
    url = base + '/makes/'
    r = requests.get(url, headers=headers, timeout=10)
    print(r)
    assert(r.status_code == 200)
    makes = r.json()['data']
    return makes


def process():
    with open('data/data.csv', 'r') as input:
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
        
       
        makes = get_makes()
        # batches = [vehicles[x:x+1000] for x in range(0, len(vehicles), 100)]
        progress = 0
        # for vehicle_batch in batches:
        t = log()
        [get_payload(v, makes) for v in vehicles]  # model_toks and payload for each vehicle

        unavailable_vehicles = [v for v in vehicles if int(v.payload['year']) < 1999]
        available_vehicles = [v for v in vehicles if v not in unavailable_vehicles]

        get_vifnums(available_vehicles)
        get_colors(available_vehicles)
        get_resource_urls(available_vehicles)
        [select_resources(v) for v in available_vehicles]
        print("\n>>>>> Sucessfully selected resource! <<<<<\n")
        beepy.beep(sound=1)

        pipe_make_images(vehicles)
        progress += len(vehicles)
        now = datetime.now()
        diff = t - now
        print("\n-------------- SUCCESS {}/{} : ∆{} ---------------".format(progress, len(vehicles), diff))
        beepy.beep(sound=5)
        time.sleep(3)


if __name__ == "__main__":
    # TODO: get API key from env variable to ensure security
    
    # session = requests.Session()
    # session.headers.update(headers)

    
    print("\n-----------------------------------------------\n")

    try:
        process()
        err504.close()
        err1040.close()
        beepy.beep(sound=5)
    except Exception as e:
        err504.close()
        err1040.close()
        beepy.beep(sound=3)
        traceback.print_exc()
        print(e)
