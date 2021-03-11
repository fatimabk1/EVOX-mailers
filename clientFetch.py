from faster import reader
import traceback
from aiohttp import ClientSession, ClientTimeout, TCPConnector, DummyCookieJar
import asyncio
import config
import json
import requests
import pypeln as pl
import time
# from pypeln.task import TaskPool


headers = {'x-api-key': config.api_key}


async def fetch(url, params, session):
    if params is not None:
        async with session.get(url, params=params) as response:
            result = await response.text()
    else:
        async with session.get(url) as response:
            result = await response.text()
        
    # return input on error
    try:
        result = json.loads(result)
        if 'statusCode' not in result and 'status' not in result:
            result = [url, params]
    except:
        result = [url, params]
    return result


async def bound_fetch(sem, url, params, session, index):
    # Getter function with semaphore.
    async with sem:
        result = await fetch(url, params, session)
        # print("\t[fetch(): {} fetched!]".format(index))
        return result 

# async def fetch(f, session):
#     if len(f) == 2:
#         async with session.get(f[0], params=f[1]) as response:
#             print("\tfetching!")
#             result = await response.text()
#     else:
#         async with session.get(f[0]) as response:
#             print("\tfetching!")
#             result = await response.text()
    
#     # return input on error
#     if "1040" in result.lower() or "504" in result.lower():
#         result = [url, params]
#     return result
   


# async def fetch_all(fetches):
#     urls = [f[0] for f in fetches]
#     params = [f[1] for f in fetches]
#     results = await pl.task.each(
#                         fetch,
#                         fetches,
#                         workers=1000,
#                         on_start=lambda: dict(session=ClientSession(connector=TCPConnector(limit=50))),
#                         on_done=lambda session: session.close(),
#                         run=True,
#                     )
#     print("all results fetched")
#     return results


# async def pl_fetch_all(fetches):
#     tasks = []
#     timeout = ClientTimeout(total=300)
#     connector = TCPConnector(limit_per_host=50)

#     index = 0
#     async with ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
        
        

        # TaskPool() as pool:
        # if len(fetches[0]) == 1:  # no paramaters
        #     for f in fetches:
        #         await pool.put(fetch(f[0], None, session, index))
        #         index += 1
        # else:  # has paramaters
        #     for f in fetches:
        #         await pool.put(fetch(f[0], f[1], session, index))
        #         index += 1
        # results = await asyncio.gather(*tasks)
        # return results


async def fetch_all(fetches, loop):
    tasks = []
    timeout = ClientTimeout(total=300)
    connector = TCPConnector(limit_per_host=50)
    sem = asyncio.Semaphore(100)

    index = 0
    async with ClientSession(loop=loop, connector=connector, timeout=timeout, headers=headers) as session:
        if len(fetches[0]) == 1:  # no paramaters
            for fetch in fetches:
                task = asyncio.ensure_future(bound_fetch(sem, fetch[0], None, session, index))
                tasks.append(task)
                index += 1
        else:  # has paramaters
            for fetch in fetches:
                task = asyncio.ensure_future(bound_fetch(sem, fetch[0], fetch[1], session, index))
                tasks.append(task)
                index += 1
        results = await asyncio.gather(*tasks)
        print("[fetch_all(): Initial results gathered!]")
        print(len([r for r in results if type(r) is list]), " failed fetches...")
        i = 0
        for index, r in enumerate(results):
            if type(r) is list:
                # try again
                print("\tfetch_all(): fetching failed request {}".format(i))
                i += 1
                retry_count = 0
                while True:
                    res = requests.get(r[0], r[1], headers=headers, timeout=300)
                    res.encoding = 'utf-8'
                    text = res.text
                    # print(text, '\n')
                    if "status" not in text:
                        print("NO STATUS CODE:", r[1])
                        time.sleep(1)
                        retry_count += 1
                        if retry_count == 10:
                            print("MAXED OUT RETRY COUNT")
                            break
                    else:
                        results[index] = res.json()
                        break

        print("[fetch_all(): All failed fetches handled!]")
        return results


# def error_hack_fetch_all(url_list, payload_list):
#     fetches = []
#     for index,u in enumerate(url_list):
#         fetches.append([u, payload_list[index]])

#     all_results = []
#     while True:
#         loop = asyncio.get_event_loop()
#         results = loop.run_until_complete(fetch_all(fetches, loop))
#         all_results = all_results + [r for r in results if type(r) is not list]
#         fetches = [r for r in results if type(r) is list]

#         print("\n", len(fetches), " failed fetches:")
#         [print("\t", f) for f in fetches]

#         if len(fetches) == 0:
#             final_results = []
#             for r in all_results:
#                 try:
#                     print("\tloading data")
#                     data = json.loads(r)
#                     final_results.append(data)
#                     print("\tall results gathered")
#                     return all_results
#                 except Exception as e:
#                     print("\n***ERROR W/JSON.LOADS()***")
#                     print(r)
#                     traceback.print_exc()
#                     print(e)
#                     exit(1)  

