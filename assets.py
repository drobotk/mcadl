#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import sys
import os
import hashlib

try:
    import uvloop
    uvloop.install()
except:
    pass

ASSETS_DOWNLOAD_URL = "https://resources.download.minecraft.net/{head}/{hash}"

async def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} path/to/index.json")
        print("\nERROR: no index file provided")
        return 1

    try:
        with open(sys.argv[1], "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("ERROR: no such file")
        return 1
    except json.JSONDecodeError:
        print("ERROR: failed to parse index as JSON")
        return 1

    try:
        os.mkdir("objects")
    except FileExistsError:
        pass

    for i in range(256):
        try:
            os.mkdir(f"objects/{i:02x}")
        except FileExistsError:
            pass

    hashes: list[str] = [o["hash"] for o in data["objects"].values()]

    def make_path(hash: str) -> str:
        return f"objects/{hash[:2]}/{hash}"

    def verify(hash: str) -> bool:
        path = make_path(hash)
        if not os.path.exists(path):
            return False
        
        with open(path, "rb") as f:
            if hashlib.sha1(f.read()).hexdigest() != hash:
                return False

        return True

    async with aiohttp.ClientSession() as s:
        async def try_download(hash: str) -> str | None:
            async with s.get(ASSETS_DOWNLOAD_URL.format(head=hash[:2], hash=hash)) as r:
                if not r.ok:
                    print(f"ERROR: {hash}: status code {r.status}")
                    return hash
                try:
                    with open(make_path(hash), "wb") as f:
                        f.write(await r.read())
                except Exception as e:
                    print(f"ERROR: {hash}: {e.__class__.__name__}: {e}")
                    return hash
        
        while hashes:
            hashes = list(filter(lambda hash: not verify(hash), hashes))
            print(f"Need to download {len(hashes)} hashes")
            ret = await asyncio.gather(*(try_download(hash) for hash in hashes))
            hashes = list(filter(None, ret))

    print("All done")

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
