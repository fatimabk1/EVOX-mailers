import csv
import asyncio
from datetime import datetime
import requests
import traceback
import config
import clientFetch
import output_check
import process_image
import animation

base = 'http://api.evoximages.com/api/v1'
err_vehicle = open('err_vehicle.txt', 'w')
err_resource = open('err_resource.txt', 'w')


class Vehicle:
    def __init__(self, vin, string, position, customer):
        self.position = position
        self.vin = vin
        self.string = string
        self.year = None
        self.make = None
        self.model = None
        self.vifnum = None  # set to None if no matching vehicle in database
        self.productTypeId = None
        self.code_len = None
        self.code_to_color = {}
        self.resources = None
        self.selected_resource = None
        self.customer = customer
    
def get_best_match(vehicle, match_list):
    vifnum = None
    if match_list is None:
        return None
        # print("BEST MATCH - no match_list given", vehicle.payload)

    if match_list is not None:
        best_match = None
        best_count = 0
        # print(f"\nmatching for {vehicle.string}")
        for match in match_list:
            # print("\t> testing ", match['vehicle_str'])
            match_str = match['vehicle_str'].lower()
            count = 0
            for tok in vehicle.model:
                if tok.lower() in match_str:
                    count += 1
            if count > best_count:
                best_count = count
                best_match = match
        # if best_count == len(vehicle.model):
        if best_count > 0:
            # print("\t\t> SELECTED: ", best_match['vehicle_str'])
            return best_match['vifnum']
        else:
            pass
            # print(f"BEST MATCH FAIL: {vehicle.string} | {vehicle.payload}", file=err_vehicle)
    return vifnum


def get_payload(vehicle, makes):   
    string = vehicle.string
    tokens = str.split(string)
    year = tokens[0]

    # convert make excel->database
    make = None
    index = 1
    m = tokens[index]
    in_list = m.lower() in (mk.lower() for mk in makes)
    if in_list:
        make = m
    else:
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
            print("INVALID MAKE: {}".format(vehicle.string), file=err_vehicle)

    model_string = ' '.join(tokens[index + 1:])
    model = None

    # FIX DODGE / RAM MAKE CONFUSION
    if make == "Dodge" and int(year) > 2010 and model_string[:3] == "Ram":
        make = "RAM"
        model_string = model_string[3:]
    
    if model_string == "Ram Pickup 1500 Srt-10":
        model = "Ram Pickup 1500"
    
    # CHEVROLET
    elif model_string == "Silverado 3500Hd Cc":
        model = "Silverado 3500HD"
    elif model_string == "Silverado 3500Hd":
        model = "Silverado 3500"
    elif model_string == "Silverado 2500Hd Classic":
        model = "Silverado Classic 2500"
    elif model_string == "Silverado 3500 Classic":
        model = "Silverado 3500"
    elif model_string == "Silverado 2500Hd":
        model = "Silverado 2500"
    elif model_string == "Silverado 3500Hd Cc":
        model = "Silverado 3500HD"
    elif model_string == "Silverado 1500Hd Classic":
        model = "Silverado Classic 1500"
    elif model_string == "Silverado 1500 Hybrid":
        model = "Silverado 1500"
    
    # MERCEDES BENZ
    elif model_string == "Sl 63 Amg":
        model = "S-Class S63 AMG"
    elif model_string == "Gl 550 4Matic":
        model = "GL-Class GL550"
    elif model_string == "E 350 Luxury":
        model = "E-Class E350"
    elif model == "E 350 Sport":
        model = "E-Class E350"
    elif model_string == "C 350 Sport":
        model = "C-Class"
    elif model_string == "C 300 Sport 4Matic":
        model = "C-Class C300"
    elif model_string == "C 250 Luxury":
        model = "C-Class C250"
    elif model_string == "E 320 Bluetec":
        model = "E-Class"
    elif model_string == "C 300 Sport":
        model = "C-Class C300"
    elif model_string == "C 300 Luxury":
        model = "C-Class C300"
    elif model_string == "C 230 Kompressor":
        model = "C-Class"
    elif model_string == "C 300 Luxury 4Matic":
        model = "C-Class"
    elif model_string == "Ml 350 4Matic":
        model = "M-Class ML350"
    elif model_string == "Ml 320 Cdi":
        model = "M-Class"
    elif model_string == "Sl 500":
        model = "SL-Class"
    elif model_string == "S 430":
        model = "S-Class"
    elif model_string == "E 320 Bluetec":
        model = "E-Class"
    elif model_string == "E 350 Luxury 4Matic":
        model = "E-Class E350"
    elif model_string == "S 550 4Matic":
        model = "S-Class S550"
    elif model_string == "Gl 450 4Matic":
        model = "GL-Class GL450"
    elif model_string == "C 230 Sport":
        model = "C-Class"

    
    # FORD
    elif model_string == "F-250 Super Duty":
        model = "F-250 SD"
    elif model_string == "F-350 Super Duty":
        model = "F-350 SD"
    elif model_string == "F-450 Super Duty":
        model = "F-450 SD"
    elif model_string == "E-Series Cargo":
        model = "Cargo"
    
    # BMW
    elif model_string == "325I":
     model = "3-series 325"
    elif model_string == "Gl 550 4Matic":
        model = "GL-Class"
    elif model_string == "525I":
        model = "5-series"
    elif model_string == "325I":
        model = "3-series 325xi"
    elif model_string == "325Ci":
        model = "3-series 325i"
    elif model_string == "750I Xdrive":
        model = "xDrive"
    elif model_string == "528I":
        model = "5-series 528"
    elif model_string == "750Li":
        model = "7-series 750"
    elif model_string == "323I":
        model = "3-series"
    
    # GMC
    elif model_string == "Sierra 2500Hd":
        model = "Sierra 2500"
    elif model_string == "Sierra 2500Hd Classic":
        model = "Sierra Classic 2500"
    elif model_string == "Sierra 3500":
        model = "Sierra"
    
    # OTHER
    elif model_string == "Cts-V":
        model = "CTS V"
    elif model_string == "Xk-Series":
        model = "XK"
    elif model_string == "Xk-Series":
        model = "XK"
    elif model_string == "B-Series Pickup":
        model = " B "
    elif model_string == "Neon Srt-4":
        model = "Neon"
    elif model_string == "Ct200h":
        model = "CT 200h"

    else:
        model = model_string

    assert(model is not None)
    model_toks = str.split(model)

    if "pickup" in model_toks:
        model_toks.remove("pickup")
    vehicle.year = year
    vehicle.make = make
    vehicle.model = model_toks
    vehicle.payload = {'year': year,
                       'make': make,
                       'model': model_toks}


@animation.wait(animation='spinner', text='\nCollecting color options ')
def get_colors(vehicles):
    # set of unique color fetches (no redundancy)
    seen = []
    [seen.append(v.vifnum)
    for v in vehicles
    if v.vifnum is not None and v.vifnum not in seen]

    fetches = [[base + '/vehicles/' + str(vifnum) + '/colors', None]
                for vifnum in seen]
    color_results = asyncio.run(clientFetch.sem_fetch_all(fetches))

    color_lookup = {}
    for result in color_results:
        # print(result)
        vifnum = result['data']['colors'][0]['vifnum']
        color_lookup[vifnum] = result['data']['colors']
    
    # print(len(color_results))
    assert(len(color_results) > 1)

    index = 0
    color_pool = ['White', 'Silver', 'Blue', 'Black', 'Gray']
    for v in vehicles:
        if v.vifnum is None:
            continue
        else:
            colors = color_lookup[v.vifnum]
            for item in colors:
                clr = item['simpletitle']
                # save codes of preferred colors
                if clr in color_pool:
                    v.code_to_color[item['code']] = clr
            v.code_len = len(colors[0]['code'])
            index += 1


@animation.wait(animation='spinner', text='\nCollecting image urls ')
def get_resource_urls(vehicles: list, resolution: int):
    for v in vehicles:
        year = int(v.year)
        # TODO: code to select productTypeId based on resolution as well
        if year < 2007:
            v.productTypeId = '235'
        else:
            v.productTypeId = '237'

    seen = []
    [seen.append((v.vifnum, v.productTypeId))
    for v in vehicles
    if v.vifnum is not None and (v.vifnum, v.productTypeId) not in seen]

    fetches = [[base + '/vehicles/' + str(tpl[0]) + '/products/29/' + str(tpl[1]), None] 
                for tpl in seen]
    resource_results = asyncio.run(clientFetch.sem_fetch_all(fetches))
    resource_lookup = {}
    for result in resource_results:
        vifnum, typeId = str(result['vehicle']['vifnum']), str(result['product']['product_type_id'])
        # print(f"\tadding key: {vifnum} --> {type(vifnum)}, {typeId} --> {type(typeId)}")
        resource_lookup[(vifnum, typeId)] = result['urls']

    # assert(len(resource_results) > 4000)

    index = 0
    count = 0
    for vehicle in vehicles:
        if vehicle.vifnum is None:
            count +=1 
            continue
        else:
            # print(f"{vehicle.vifnum} --> {type(vifnum)}, {vehicle.productTypeId} --> {type(typeId)}")
            vehicle.resources = resource_lookup[(str(vehicle.vifnum), vehicle.productTypeId)]
            index += 1
    print(count, "vehicles with no vifnum")


def select_resources(vehicle):
    if vehicle.resources is None:
        return

    resource_urls =  vehicle.resources
    assert(len(resource_urls) > 0)
    code_to_color = vehicle.code_to_color
    code_start = len(resource_urls[0]) - 4 - vehicle.code_len
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
    
    # assign random colored image if preferred colors unavailable
    if vehicle.selected_resource is None:
        vehicle.selected_resource = resource_urls[0]
        print(f"selecting random image color: {vehicle.string} | {vehicle.payload}")


def get_makes():
    url = base + '/makes/'
    retry_count = 0
    while True:
        r = requests.get(url, headers=config.headers, timeout=10)
        if r.status_code == 200:
            break
        else:
            retry_count += 1
            if retry_count == 5:
                print("FAILURE: get_makes() server error")
                exit(1)

    makes = r.json()['data']
    return makes


def get_vehicle_matches(vehicles):
    url = base + '/vehicles'
    fetches = []
    for v in vehicles:
        if [url, {'year': v.year, 'make': v.make}] in fetches:
            continue
        else:
            fetches.append([url, {'year': v.year, 'make': v.make}])
    vifnum_results = asyncio.run(clientFetch.sem_fetch_all(fetches))

    vehicle_lookup = {}  # (year, make) --> vehicle results
    index = 0
    for fetch in fetches:
        key = (fetch[1]['year'], fetch[1]['make'])
        vehicle_lookup[key] = vifnum_results[index]
        index += 1

    cached_matches = {}  # (year, make, model) --> vifnum of best match 
    for v in vehicles:

        key = v.payload.values()
        # found this match previously
        if key in cached_matches:
            if cached_matches[key] is not  None:
                v.vifnum = cached_matches[key]
        else:
            # one or more matches
            if vehicle_lookup[(v.year, v.make)]['statusCode'] == 200:
                vifnum = get_best_match(v, vehicle_lookup[(v.year, v.make)]['data'])
                cached_matches[key] = vifnum
                v.vifnum = vifnum
                assert(cached_matches[key] == vifnum)
            # no matches
            elif vehicle_lookup[(v.year, v.make)]['statusCode'] == 404:
                cached_matches[key] = None
                print(f"404 no matches: {v.string}, | {v.payload}", file=err_vehicle)


def process(input_file: str, target_folder: str, resolution: int):
    t = datetime.now()
    print(f"start: {t}")
    file = 'data/' + input_file
    with open(config.input_file, 'r') as input:
        reader = csv.DictReader(input)

        # collect vehicle strings from input
        vehicles = []
        for row in reader:
            for i in range(3):
                vin = "VIN{}".format(i + 1)
                vehicle = "Vehicle{}".format(i + 1)
                if row[vin]:
                    v = Vehicle(row[vin], row[vehicle], i + 1, row["ControlNum"])
                    vehicles.append(v)

        # extract year, make, model from vehicle string
        makes = get_makes()
        [get_payload(v, makes) for v in vehicles]  

        # Assign vifnums & cache db vehicle data as we go
        # wait = animation.Wait(animation='bar', text='\nSearching for vehicle matches ')
        # wait.start()
        eligible_vehicles = [v for v in vehicles if int(v.year) >= 2000] 
        old_vehicle_count = len(vehicles) - len(eligible_vehicles)
        print(f"{old_vehicle_count}/{len(vehicles)} vehicles are older than 2000 and not in EVOX database")
        get_vehicle_matches(eligible_vehicles)
        uncaught_miss_count = 0
        uncaught_misses = {}
        for v in eligible_vehicles:
            if v.vifnum is None:
                if v.string in uncaught_misses:
                    uncaught_misses[v.string] += 1
                    uncaught_miss_count += 1
                else:
                    uncaught_misses[v.string] = 1
                    uncaught_miss_count += 1

        print(f"{uncaught_miss_count}/{len(eligible_vehicles)} checked vehicles do not have matches in database.",
                "See err_vehicle.txt for details.")

        print("\nDATABASE MISSES:", file=err_vehicle)
        print("\nDATABASE MISSES:")
        for miss in uncaught_misses:
            print(miss, uncaught_misses[miss], file=err_vehicle)
            print(miss, uncaught_misses[miss])
        # wait.stop()

        # pull colors, urls, and select url w/preferred color
        get_colors(eligible_vehicles)
        get_resource_urls(eligible_vehicles, resolution)
        [select_resources(v) for v in eligible_vehicles]

        # make all images
        count = 0
        customer_stats = {}
        print("\n")
        for v in vehicles:
            if v.customer not in customer_stats:
                customer_stats[v.customer] = [0, 0]  # silhouttes, total vehicles
            customer_stats[v.customer][1] += 1
            if v.selected_resource is None:
                customer_stats[v.customer][0] += 1
                v.selected_resource = 'silhouette.jpg'
                # print(f"FOUND SILHOUETTE: {v.string} | {v.payload}", file=err_vehicle)
                count += 1

        print(f"silhouette count = {count}. See customer_miss.txt for breakdown by customer")
        for customer in customer_stats:
            if customer_stats[customer][0] > 0:
                print(f"{customer} : {customer_stats[customer][0]}/{customer_stats[customer][1]} vehicles are silhouettes.", file=err_customer)
                print(f"{customer} : {customer_stats[customer][0]}/{customer_stats[customer][1]} vehicles are silhouettes.")

        tasks = [(v.selected_resource, v.vin) for v in vehicles]
        print("\n")
        expected_time = round(len(tasks) / 500) * 4
        now = datetime.now()
        txt = f"Starting download for {len(tasks)} images [{now.hour}:{now.minute}:{now.second}]. Expected wait: {expected_time}s"
        wait = animation.Wait(animation='bar', text=txt)
        wait.start()
        asyncio.run(process_image.download_all(tasks, target_folder))
        wait.stop()

        now = datetime.now()
        delta = now - t
        print(f"Downloads complete [{now.hour}:{now.minute}:{now.second}].\n> Total program runtime = {delta}")


def run(input_file: str, target_folder: str,resolution: int):
    try:
        err_customer = open('customer_miss.txt', 'w')
        err_vehicle = open('err_vehicle.txt', 'w')
        err_resource = open('err_resource.txt', 'w')
        process(input_file, target_folder, resolution)
        err_vehicle.close()
        err_resource.close()
        output_check.check()
    except Exception as e:
        err_customer.close()
        err_vehicle.close()
        err_resource.close()
        print("Process Failed.")
        traceback.print_exc()
        print(e)
