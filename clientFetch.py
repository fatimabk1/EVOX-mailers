from aiohttp import ClientSession, TCPConnector
import asyncio
from datetime import datetime
import config



async def fetch(url, params, session):
    retry_count = 0
    while True:
        # fetch endpoint
        if params:
            response = await session.get(url, params=params, headers=config.headers)
        else:
            response = await session.get(url, headers=config.headers)
        
        # handle errors
        if response.status == 200 or response.status == 404:
            result = await response.json()
            break
        else:
            retry_count += 1
            if retry_count == 5:
                print(f"\t> FAILURE: fetch() retry_count maxed out -- {params} | {url}")
                exit(1)
    return result


async def bound_fetch(sem, url, params, session):
    # Getter function with semaphore.
    async with sem:
        result = await fetch(url, params, session)
        return result 

async def fetch_all(fetches):
    connector = TCPConnector(limit_per_host=50)
    tasks = []
    results = []
    async with ClientSession(connector=connector, headers=config.headers) as session:
        index = 0
        batches = [fetches[i:i + 1000] for i in range(0, len(fetches), 1000)]
        for batch in batches:
            for fetch_task in batch:
                t = asyncio.create_task(fetch(fetch_task[0], fetch_task[1], session))
                tasks.append(t)
            results.append(await asyncio.gather(*tasks))
            index += 1
        if len(results) == 1:
            return results[0]
        return results       
