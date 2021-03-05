import csv
import requests
import json
import traceback
import imageio
import random
from datetime import datetime, timedelta
import beepy
import config


def log():
    return datetime.now()


def delta(msg, start):
    curr = datetime.now()
    print(msg + "∆: ", curr - start)


def get_makes(session, base, headers):
    url = base + '/makes/'
    t = log()
    r = session.get(url, headers=headers, timeout=10)
    delta("\tdb query makes", t)
    assert(r.status_code == 200)
    makes = r.json()['data']
    return makes


def get_payload(session, vehicle, makes):        
    tokens = str.split(vehicle)
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

    print("model_toks: ", model_toks)

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
        #     pass
        
    print("model = ", model_toks)
    payload = {'year': year,
               'make': make,
               'model': model_toks}
    return payload


# payload[make] needs to be a list of tokens
def get_vifnum(session, base, payload, headers, nonexistent):
    og_payload = payload
    model = payload['model']
    payload = {'year': payload['year'], 'make': payload['make']}
    list_a = model
    list_b = []

    while True:
        payload['model'] = ' '.join(list_a)
        print(payload)

        url = base + '/vehicles'
        t = log()
        r = session.get(url, params=payload, headers=headers, timeout=10)
        delta("\tdb query vehicles", t)
        result = r.json()

        # NO MATCHES
        if r.status_code != 200:
            if len(list_a) == 0:
                # VEHICLE NOT IN DATABASE
                del payload['model']
                print("no vifnum match: ", og_payload, file=nonexistent)
                return None
            else:
                # TRY A LESS SPECIFIC VERSION
                tok = list_a.pop()
                list_b.insert(0, tok)

        # MATCHES
        else:
            vehicles = result['data']
            if len(vehicles) == 1:
                return vehicles[0]['vifnum']
            else:
                for vehicle in vehicles:
                    match = True
                    vehicle_str = vehicle['vehicle_str'].lower()
                    for tok in list_b:
                        if tok.lower() not in vehicle_str:
                            match = False
                    if match is True:
                        return vehicle['vifnum']
                return vehicles[0]['vifnum']


def get_colors(session, base, headers, vifnum):
    # PULL COLOR CODE LIST
    t = log()
    color_pool = ["White", "Silver", "Blue", "Black", "Gray"]
    url = base + '/vehicles/' + str(vifnum) + '/colors'
    t = log()
    r = session.get(url, headers=headers, timeout=10).json()
    delta("\tdb query color codes", t)
    colors = r['data']['colors']
    color_to_code = {}
    code_to_color = {}
    for item in colors:
        clr = item['simpletitle']
        if clr in color_pool:
            # color_codes[clr] = item['code']
            color_to_code[clr] = item['code']
            code_to_color[item['code']] = clr
    delta("pull color code list", t)
    return color_to_code, code_to_color


def get_resource_urls(session, base, payload, vifnum, nonexistent):
    t = log()
    productId = '29'
    if int(payload['year']) < 2007:
        productTypeId = '235'  # angle 001
    else:
        productTypeId = '237'  # angle 032
    db_call = log()
    url = base + '/vehicles/' + str(vifnum) + '/products/' + str(productId) + '/' + str(productTypeId)
    r = session.get(url, headers=headers, timeout=10)
    delta("\tdb query resource ulrs", db_call)
    if r.status_code != 200:
        print(">>> no stills for : ", payload)
        print(">>> no stills for : ", payload, file=nonexistent)
        resource = 'sillhouette.jpg'
        return vifnum, [resource, resource, resource]
    delta("pull resource urls", t)
    return r.json()['urls'] 


def save_urls(session, base, payload, headers, nonexistent):
    og_payload =  payload
    t = log()
    vifnum = get_vifnum(session, base, payload, headers, nonexistent)
    delta("get_vifnum()", t)

    payload['model'] = ' '.join(payload['model'])
    if vifnum is None:
        return None, None
    print("vifnum = {}, year = {}, make = {}, model = {}"
        .format(vifnum, payload['year'], payload['make'], payload['model']))
    
    color_to_code, code_to_color = get_colors(session, base, headers, vifnum)
    resource_urls =  get_resource_urls(session, base, payload, vifnum, nonexistent)

    t = log()
    # SAVE ALL IMAGES W/MOST PREFERRED AVAILABLE COLORS
    main_count = 0
    general_count = 0
    possible_images = {}
    images = [None, None, None]

    codes = list(color_to_code.values())
    code_start = len(resource_urls[0]) - 4 - len(codes[0])
    code_end = len(resource_urls[0]) - 4
    for resource in resource_urls:
        resource_color_code = resource[code_start:code_end]
        if resource_color_code in code_to_color:
            clr = code_to_color[resource_color_code]
            if clr == "White":
                main_count += 1
                general_count += 1
                images[1] = resource
            elif clr == "Silver":
                main_count += 1
                general_count += 1
                images[2] = resource
            elif clr == "Blue":
                main_count += 1
                general_count += 1
                images[0] = resource
            elif clr == "Black":
                general_count += 1
                possible_images["Black"] = resource
            elif clr == "Gray":
                general_count += 1
                possible_images["Gray"] = resource
            else:
                continue
    print(images)
    delta("save all preffered imgs & colors", t)

    # SAVE IMAGES W/MOST PREFFERED COLOR OF AVAILABILE COLORS
    if main_count == 3:
        # case 1 - blue, white, silver
        return vifnum, images
    
    elif len(possible_images.keys()) == 0:
        return vifnum, [resource, resource, resource]
  
    else:
        t = log()
        if images[0] is None:  # blue is missing
            # case 2 - preferred backup color
            if "Black" in possible_images:
                images[0] = possible_images["Black"]
            elif "Gray" in possible_images:
                images[0] = possible_images["Gray"]
            else:
                # case 3 - repeat from whatever colors we have
                clr = random.sample(possible_images.keys(), 1)
                images[1] = possible_images[clr]
    
        if images[1] is None:  # white is missing
            if "Black" in possible_images:
                images[1] = possible_images["Black"]
            elif "Gray" in possible_images:
                images[1] = possible_images["Gray"]
            else:
                clr = random.sample(possible_images.keys(), 1)
                images[1] = possible_images[clr]
        
        if images[2] is None:  # silver is missing
            if "Gray" in possible_images:
                images[2] = possible_images["Gray"]
            elif "Black" in possible_images:
                images[2] = possible_images["Black"]
            else:
                # print(possible_images.keys())
                clr = random.sample(possible_images.keys(), 1)
                images[2] = possible_images[clr]
        delta("save preferred images colors", t)
    print("images: ", images)
    # delta("save top 3 priority colored images", t)
    return vifnum, images

def make_image(resource, vin):
    save_path = "images/" + vin + ".jpg"
    if resource == "sillhouette.jpg":
        print("resource: " + resource)
        img_in = imageio.imread(resource, '.jpg')
    else:
        print("resource: " + resource)
        img_in = imageio.imread(imageio.core.urlopen(resource).read(), '.jpg')
    img = imageio.imwrite(save_path, img_in, format=".jpg")

def process(session, base, headers, makes):
    with open('data/data.csv', 'r') as input:
        reader = csv.DictReader(input)
        nonexistent =  open('nonexistent.txt', 'a')
        multiple = open('multiple.txt', 'a')

        mapping = {}  # { vehicle(yr/mk/mdl): { vif: vif#, red: url, white: url, blue: url }
        for row in reader:
            lookup = {
                "1": {"vin": row["VIN1"], "vehicle": row["Vehicle1"]},
                "2": {"vin": row["VIN2"], "vehicle": row["Vehicle2"]},
                "3": {"vin": row["VIN3"], "vehicle": row["Vehicle3"]}
            }
            
            
            for key in lookup:
                # completely handle one car
                one_car = log()
                vin = lookup[key]["vin"]
                vehicle = lookup[key]["vehicle"]
                # vehicle = "2006 Mercedes_Benz R-Class"
                mapping = {}

                # skip if no vehicle
                if vin is None or len(vin) == 0:  # TODO: double check this
                    continue
                
                # add vehicle to mapping if not present
                elif vehicle not in mapping:
                    print("vehicle = ", vehicle)
                    # payload = {'year': '2009', 'make': 'buick', 'model': 'enclave'}
                    t = log()
                    payload = get_payload(session, vehicle, makes)
                    delta("get_payload()", t)
                    t = log()
                    vifnum, images = save_urls(session, base, payload, headers, nonexistent)
                    delta("get_resource_urls()", t)
                    # delta("get_resource_urls()", t)
                    if vifnum is None and images is None:
                        continue
                    mapping[vehicle] = {'vif': vifnum,
                                        'Blue': images[0],
                                        'White': images[1],
                                        'Silver': images[2]}

                mapping_key = None
                if key == "1":
                    mapping_key = 'Blue'
                elif key == "2":
                    mapping_key = "White"
                elif key == "3":
                    mapping_key = 'Silver'

                print("mapping_key = ", mapping_key)
                if mapping_key is not None:
                    resource = mapping[vehicle][mapping_key]
                else:
                    resource = "sillhouette.jpg"

                t = log()
                make_image(resource, vin)
                delta("make_image()", t)

                delta("one car - loop", one_car)
                exit(0)
                print("\n-----------------------------------------------\n")
                
        nonexistent.close()
        multiple.close()


if __name__ == "__main__":
    # TODO: get API key from env variable to ensure security
    base = 'http://api.evoximages.com/api/v1'
    headers = {'x-api-key': config.api_key}
    session = requests.Session()
    session.headers.update(headers)

    t = log()
    makes = get_makes(session, base, headers)
    # delta("get_makes()", t)
    print("\n-----------------------------------------------\n")


    open('nonexistent.txt', 'w').close()
    open('multiple.txt', 'w').close()

    try:
        process(session, base, headers, makes)
        beepy.beep(sound=5)
    except Exception as e:
        beepy.beep(sound=3)
        traceback.print_exc()
        print(e)


# QUESTIONS: 

# 1. Need to handle issue where multiple matches -- diff trim/string & color title
# 2. Function to transform excel data into dictionary 
#       {'customer_id': {'v1': {'year': '', 'make': '', 'model': ''}, 'v2': {}, 'v3': {}}} 
# 4. How to select productId 29 stills (403 forbidden error) 
# 5. Confirm still to product url


# 5. Which stills am I looking for exactly? > confirm w/Jordan
