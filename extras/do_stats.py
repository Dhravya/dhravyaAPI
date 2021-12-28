import aiofiles, json

def do_statistics(endpoint_func):
    async def wrapper(*args, **kwargs):
        returned_value = await endpoint_func(*args, **kwargs)
        # Get the endpoint name
        endpoint_name = endpoint_func.__name__

        # Get the statistics using aiofiles
        async with aiofiles.open(f"./statistics.json", "r") as f:
            statistics = json.loads(await f.read())
        
        # Check if the endpoint is in the statistics
        if endpoint_name in statistics:
            # Increment the count
            statistics[endpoint_name] += 1
        else:
            # Add the endpoint to the statistics and set the count to 1
            statistics[endpoint_name] = 1

        # Write the statistics back to the file
        async with aiofiles.open(f"./statistics.json", "w") as f:
            await f.write(json.dumps(statistics))

        
        return returned_value

    return wrapper
