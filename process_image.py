import asyncio
import traceback
import aiohttp
import aiofiles
import config
import resource
import os

# ------------------------------------------------------------------- ASYNCHRONOUS IMAGE DOWNLOADING
async def download_image(target_folder, url, image_name, session):
    save_path = os.path.join(target_folder, image_name + '.jpg')
    retry_count = 0
    while True:
        try:
            if url == "silhouette.jpg":
                async with aiofiles.open(save_path, mode='wb') as f:
                    async with aiofiles.open('silhouette.jpg', 'rb') as source:
                        await f.write(await source.read())
                        await f.close()
                        await source.close()
                        break
            else:
                async with session.get(url, headers=config.headers) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(save_path, mode='wb') as f:
                            await f.write(await resp.read())
                            await f.close()
                            break
                    else:
                        print("\t> STATUS ERROR", resp.status, "-- ", image_name, " | ", url)
                        retry_count += 1
                        if retry_count == 5:
                            print("\t\t> FATAL: retry_count maxed out. Unable to download image.")
                            exit(1)
        except Exception as e:
            retry_count += 1
            if retry_count == 5:
                print(f"\t> DOWNLOAD FAILURE: VIN {image_name} | {url}")
                traceback.print_exc()
                print(e)
                exit(1)

async def bound_download(sem, target_folder, url, image_name, session):
    async with sem:
        await download_image(target_folder, url,image_name, session)


async def download_all(fetches: list, target_folder: str):
    # increase file limit to avoid OS ERROR too many open files
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (3000, hard))

    conn = aiohttp.TCPConnector(limit_per_host=50)
    sem = asyncio.Semaphore(1500)
    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for fetch in fetches:
            t = asyncio.create_task(bound_download(sem, target_folder, fetch[0], fetch[1], session))
            tasks.append(t)
        await asyncio.gather(*tasks)
