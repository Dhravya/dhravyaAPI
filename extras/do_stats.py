import aiofiles, json

async def do_statistics(name:str):

    # Get the statistics using aiofiles
    async with aiofiles.open(f"./statistics.json", "r") as f:
        statistics = json.loads(await f.read())
    
    # Check if the endpoint is in the statistics
    if name in statistics:
        # Increment the count
        statistics[name] += 1
    else:
        # Add the endpoint to the statistics and set the count to 1
        statistics[name] = 1

    # Write the statistics back to the file
    async with aiofiles.open(f"./statistics.json", "w") as f:
        await f.write(json.dumps(statistics, indent=4))



