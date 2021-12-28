import json
from typing import Optional
import aiofiles
import aiohttp
import random
import io
import os
import dotenv

dotenv.load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse

from mcstatus import MinecraftServer
import pyfiglet
import qrcode
from qrcode.image.styledpil import StyledPilImage

from extras.qr_stuff import _styles
from extras.meme_fetcher import get_meme, topics_accepted

# Defining apps and configs.
app = FastAPI()

FIGLET_FONTS = """3-d, 3x5, 5lineoblique, alphabet, banner3-D, 
                    doh, isometric1, letters, alligator, dotmatrix, 
                    bubble, bulbhead, digital"""


@app.get("/")
async def test():
    return {"Hello": "World"}


@app.get("/8ball")
async def eightball():
    answers = [
        "It is certain",
        "It is decidedly so",
        "Without a doubt",
        "Yes definitely",
        "You may rely on it",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes",
        "Reply hazy try again",
        "Ask again later",
        "Better not tell you now",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "My reply is no",
        "My sources say no",
        "Outlook not so good",
        "Very doubtful",
    ]
    return {"success": 1, "data": {"answer": random.choice(answers)}}


@app.get("/qrcode")
async def qr_code(
    query: Optional[str] = None,
    drawer: Optional[str] = None,
    mask: Optional[str] = None,
    fg: Optional[str] = None,
    bg: Optional[str] = None,
    ):

    if not query:
        return {"success": 0, "data": {"errormessage": "You didn't give a query!"}}

    n = random.randint(1, 5)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(query)
    qr.make(fit=True)

    if not drawer:
        drawer = "1"

    if not mask:
        mask = "1"

    # CHecks if the drawer and mask is valid
    if drawer not in _styles["drawers"]:
        return {"success": 0, "data": {"errormessage": "That drawer is invalid!"}}
    if mask not in _styles["masks"]:
        return {"success": 0, "data": {"errormessage": "That mask is invalid!!"}}

    drawer = _styles["drawers"][str(drawer)]
    try:
        if fg or bg:
            img = qr.make_image(fill_color=fg, back_color=bg)
        else:
            img = qr.make_image(
                module_drawer=drawer,
                color_mask=_styles["masks"][str(mask)],
                image_factory=StyledPilImage,
            )
    except Exception as e:
        return {"success": 0, "data": {"errormessage": f"Unexpected error: {e}"}}
    img.save(f"./temp/qr_codes/{n}.png", "PNG")
    return FileResponse(f"./temp/qr_codes/{n}.png")

#!#################################################
#* Memes
#!#################################################
@app.get("/meme/{topic}")
@app.get("/memes/{topic}")
async def meme(topic: str):
    if not topic in topics_accepted:
        topic = topic + "memes"

    meme = await get_meme(topic)

    return {
        "success": 1,
        "data": {
            "url": meme["url"],
            "subreddit": meme["subreddit"],
            "title": meme["title"],
            "score": meme["score"],
            "id": meme["id"],
            "selftext": meme["selftext"],
            "is_nsfw": meme["over_18"],
        },
    }


@app.get("/meme")
async def single_meme():
    meme = await get_meme("random")

    async with aiohttp.ClientSession() as resp:
        async with resp.get(meme["url"]) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {"errormessage": "Couldn't fetch the meme!"},
                }
            else:
                meme_bytes = await resp.read()
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")

#!#################################################
#* Joke, WYR, etc generators
#!#################################################

@app.get("/wyr")
@app.get("/wouldyourather")
async def wyr():
    """Returns a would you rather question"""
    async with aiofiles.open("./data/txt/wyr.txt", "r") as f:
        data = await f.readlines()
    question = data[random.randrange(0, len(data))][:-2].split(" or ")

    return {"success": 1, "data": {"Would you rather": question}}


@app.get("/joke")
async def joke():
    """Returns a joke"""
    async with aiofiles.open("./data/txt/jokes.txt", "r") as f:
        data = await f.readlines()
    joke = data[random.randrange(0, len(data))][:-2]

    return {"success": 1, "data": {"Joke": joke}}


@app.get("/compliment")
async def compliment():
    """Returns a compliment"""
    async with aiofiles.open("./data/txt/compliments.txt", "r") as f:
        data = await f.readlines()
    compliment = data[random.randrange(0, len(data))][:-2]

    return {"success": 1, "data": {"Compliment": compliment}}


@app.get("/topic")
async def topic():
    """Returns a topic"""
    async with aiofiles.open("./data/txt/topics.txt", "r") as f:
        data = await f.readlines()
    topic = data[random.randrange(0, len(data))][:-2]

    return {"success": 1, "data": {"Topic": topic}}

#!#################################################
#* ASCII
#!#################################################

@app.get("/ascii")
async def ascii(text: Optional[str] = "No text provided", font: Optional[str] = ""):
    """Returns an ascii art"""
    try:
        result = pyfiglet.figlet_format(text, font=font)
    except Exception as e:
        return {
            "success": 0,
            "data": {
                "errormessage": f"Unexpected error: {e} Make sure your font is valid! {FIGLET_FONTS}"
            },
        }
    return {
        "success": 1,
        "data": {
            "Ascii": result,
            "accepted_fonts": f"Accepted fonts are {FIGLET_FONTS} ",
        },
    }

#!#################################################
#* Use of other apis
#!#################################################

@app.get("/songinfo")
@app.get("/song-info")
@app.get("/song_info")
async def song_info(song: str):
    GENIUS_API_URL = "https://api.genius.com"
    headers = {"Authorization": f'Bearer {os.environ["GENIUS_API_KEY"]}'}
    params = {"q": song}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            GENIUS_API_URL + "/search", params=params, headers=headers
        ) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the song info!",
                    },
                }
            data = await resp.json()
        return data

@app.get("/mcstatus")
async def mcstatus(host: str, port:str = None):
    """Returns the status of a minecraft server"""
    if not port:
        port = 25565
    try:
        server = MinecraftServer.lookup(host + ":" + str(port))
        status = server.status()
    except Exception as e:
        return {
            "success": 0,
            "data": {
                "errormessage": f"Unexpected error: {e}"
            },
        }
    
    return {
        "success": 1,
        "data": {
            "host": host,
            "port": port,
            "online": status.players.online,
            "max": status.players.max
        },
    }

#!#################################################
#* Image providers and image processing
#!#################################################

@app.get("/dogs")
@app.get("/dog")
async def dog():
    pass

@app.get("/cat")
@app.get("/cats")
async def cat():
    pass

#!#################################################
#* Undocumented, for personal use
#!#################################################

@app.get("/stats")
async def stats():
    with open("statistics.json", "r") as f:
        statistics = json.load(f)
    return {"success": 1, "data": {"statistics": statistics}}

