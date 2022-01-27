"""
Note to myself:
! TO restart the api after edits:
pkill gunicorn
gunicorn app:app -w 1 -k uvicorn.workers.UvicornWorker -b "127.0.0.1:8000" --daemon
"""

import json
from typing import Optional, Sequence, Union
import aiofiles
import aiohttp
import random
import io
import os
import aiosqlite

from fastapi import FastAPI
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    RedirectResponse,
    PlainTextResponse,
)

from mcstatus import MinecraftServer
import pyfiglet
import qrcode
from qrcode.image.styledpil import StyledPilImage
import MemePy
import googletrans

from extras.qr_stuff import _styles
from extras.meme_fetcher import get_meme, topics_accepted
from extras.memegenerator import make_meme
from extras.do_stats import do_statistics
from extras.owofy import owofy as owo_converter
from extras.britishify import strong_british_accent as british_converter

# Defining apps and configs.

description = """
This is a simple API that is meant to "Do it all" for you.
It will fetch a random meme from reddit, and generate a QR code with the URL, and much, much more!

<hr>

# Features
- QR Code Generator
- Meme Fetcher
- Minecraft Status Checker
- Meme Generator
- Jokes, Quotes, and other fun stuff
- Ascii Art Generator
- Song Information Fetcher
- Use of secret internal Google's APIs for stuff like Google Search suggestions, and more soon!
- A simple mode using ?simple=true (only works for text-related endpoints)

<hr>

## If you think you have an idea to make the API better, please let me know!
Join the Coding horizon discord server for help and support!
https://discord.gg/rqhgqTqFbp
"""

app = FastAPI(
    title="DhravyaAPI",
    description=description,
    contact={
        "name": "Dhravya Shah",
        "url": "https://dhravya.me",
        "email": "dhravyashah@gmail.com",
    },
    version="2.0",
    openapi_url="/v2/openapi.json",
)


FIGLET_FONTS = """3-d, 3x5, 5lineoblique, alphabet, banner3-D, 
                    doh, isometric1, letters, alligator, dotmatrix, 
                    bubble, bulbhead, digital"""

# add the Access-Control-Allow-Origin header to allow cross-origin requests
# from the frontend
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


#!#################################################
# * Unimportant stuff, testing, etc
#!#################################################


@app.get("/")
async def docs():
    return RedirectResponse("/docs")


@app.get("/8ball")
async def eightball(simple: Optional[str] = "False"):

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
    await do_statistics("8ball")

    if simple.lower() == "true":
        return PlainTextResponse(random.choice(answers))
    return {"success": 1, "data": {"answer": random.choice(answers)}}


#!#################################################
# * QR Code generator
#!#################################################


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
    await do_statistics("qrcode")
    return FileResponse(f"./temp/qr_codes/{n}.png")


#!#################################################
# * Memes
#!#################################################
@app.get("/meme/{topic}")
async def meme(topic: str):
    if not topic in topics_accepted:
        topic = topic + "memes"

    meme = await get_meme(topic)
    await do_statistics("meme")
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
                await do_statistics("single_meme")
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")


#!#################################################
# * TEXT-BASED | Joke, WYR, etc generators
#!#################################################


@app.get("/wyr")
async def wyr(simple: Optional[str] = "False"):
    """Returns a would you rather question"""
    async with aiofiles.open("./data/txt/wyr.txt", "r") as f:
        data = await f.readlines()
    question = data[random.randrange(0, len(data))][:-2].split(" or ")

    await do_statistics("wyr")
    if simple.lower() == "true":
        question[0] = question[0].capitalize()
        question[1] = question[1].capitalize()
        e = f"{question[0]} or {question[1]}?"
        return PlainTextResponse(e)
    return {"success": 1, "data": {"Would you rather": question}}


@app.get("/truthordare")
async def truthordare(simple: Optional[str] = "False"):
    """Returns a Truth and Dare."""
    await do_statistics("truthordare")
    async with aiofiles.open("./data/txt/truth.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    question = data[random.randrange(0, len(data))][:-1]

    async with aiofiles.open("./data/txt/dare.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    question2 = data[random.randrange(0, len(data))][:-1]

    if simple.lower() == "true":
        return PlainTextResponse(f"{question} - {question2}")
    return {"success": 1, "data": {"Truth": question, "Dare": question2}}


@app.get("/fact")
async def fact(simple: Optional[str] = "False"):
    """Returns a Fact."""
    await do_statistics("fact")
    async with aiofiles.open("./data/txt/facts.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    fact = data[random.randrange(0, len(data))][:-1]

    if simple.lower() == "true":
        return PlainTextResponse(f"{fact}")
    return {"success": 1, "data": {"Fact": fact}}


@app.get("/roast")
async def roast(simple: Optional[str] = "False"):
    """Returns a Roast."""
    await do_statistics("roast")
    async with aiofiles.open("./data/txt/roasts.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    roast = data[random.randrange(0, len(data))][:-1]

    if simple.lower() == "true":
        return PlainTextResponse(f"{roast}")
    return {"success": 1, "data": {"Roast": roast}}


@app.get("/trivia")
async def trivia(simple: Optional[str] = "False"):
    """Returns a Trivia Question."""
    await do_statistics("trivia")
    async with aiofiles.open("./data/txt/trivia.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    trivia = data[random.randrange(0, len(data))][:-1]
    trivia = trivia.split(" | ")

    if simple.lower() == "true":
        return PlainTextResponse(f"{trivia[0]}\n{trivia[1]}")
    return {
        "success": 1,
        "data": [{"Question": trivia[0], "Answer": trivia[1]}],
    }


@app.get("/truth")
async def truth(simple: Optional[str] = "False"):
    """Returns a Truth."""
    await do_statistics("truthordare")
    async with aiofiles.open("./data/txt/truth.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    question = data[random.randrange(0, len(data))][:-1]

    if simple.lower() == "true":
        return PlainTextResponse(f"{question}")
    return {"success": 1, "data": {"Truth": question}}


@app.get("/dare")
async def truth(simple: Optional[str] = "False"):
    """Returns a Dare."""
    await do_statistics("truthordare")
    async with aiofiles.open("./data/txt/dare.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    question = data[random.randrange(0, len(data))][:-1]

    if simple.lower() == "true":
        return PlainTextResponse(f"{question}")
    return {"success": 1, "data": {"Dare": question}}


@app.get("/joke")
async def joke(simple: Optional[str] = "False"):
    """Returns a joke"""
    async with aiofiles.open("./data/txt/jokes.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    joke = data[random.randrange(0, len(data))][:-1]

    await do_statistics("joke")
    if simple.lower() == "true":
        return PlainTextResponse(joke)
    return {"success": 1, "data": {"Joke": joke}}


@app.get("/compliment")
async def compliment(simple: Optional[str] = "False"):
    """Returns a compliment"""
    async with aiofiles.open("./data/txt/compliments.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    compliment = data[random.randrange(0, len(data))][:-1]

    await do_statistics("compliment")
    if simple.lower() == "true":
        return PlainTextResponse(compliment)
    return {"success": 1, "data": {"Compliment": compliment}}


@app.get("/neverhaveiever")
async def neverhaveiever(simple: Optional[str] = "False"):
    """Returns a Never Have I Ever."""
    async with aiofiles.open(
        "./data/txt/neverhaveiever.txt", "r", encoding="utf8"
    ) as f:
        data = await f.readlines()
    nhie = data[random.randrange(0, len(data))][:-1]

    await do_statistics("neverhaveiever")
    if simple.lower() == "true":
        return PlainTextResponse(nhie)
    return {"success": 1, "data": {"Topic": nhie}}


@app.get("/topic")
async def topic(simple: Optional[str] = "False"):
    """Returns a topic"""
    async with aiofiles.open("./data/txt/topics.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    topic = data[random.randrange(0, len(data))][:-2]

    await do_statistics("topic")
    if simple.lower() == "true":
        e = f"{topic}?"
        return PlainTextResponse(e)
    return {"success": 1, "data": {"Topic": topic}}

@app.get("/owofy")
async def owofy(text: Optional[str] = "No text provided", wanky: Optional[str] = "False", simple: Optional[str] = "False"):
    await do_statistics("owofy")
    wanky = False if wanky.lower() == "false" else True
    owo_text = owo_converter(text=text, wanky=wanky)

    if simple.lower() == "true" and isinstance(text, str):
        return PlainTextResponse(owo_text)
    
    return {"success": 1, "data": {"wanky": int(wanky), "owo_text": owo_text}}

@app.get("/britify")
async def britify(text: Optional[str] = "No text provided", simple: Optional[str] = "False"):
    await do_statistics("britify")
    british_text = british_converter(text=text)

    if simple.lower() == "true" and isinstance(text, str):
        return PlainTextResponse(british_text)
    
    return {"success": 1, "data": {"british_text": british_text}}


# Initialising the Translator
translator = googletrans.Translator()


@app.get("/translate")
async def translate(
    text: str, from_lang: str, to_lang: str = "en", simple: Optional[str] = "False"
):
    """Returns a translated text"""
    if not from_lang in googletrans.LANGCODES.values():
        return {
            "success": 0,
            "data": {
                "errormessage": "Invalid language! Language should be in the available languages.",
                "available_languages": googletrans.LANGCODES,
            },
        }

    await do_statistics("translate")
    result = translator.translate(text, src=from_lang, dest=to_lang)
    result = result.text
    if simple.lower() == "true":
        return PlainTextResponse(result)
    return {"success": 1, "data": {"Translation": result}}


#!#################################################
# * ASCII
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

    await do_statistics("ascii")
    return {
        "success": 1,
        "data": {
            "Ascii": result,
            "accepted_fonts": f"Accepted fonts are {FIGLET_FONTS} ",
        },
    }


#!#################################################
# * Use of other apis
#!#################################################


@app.get("/lyrics")
async def lyrics(song: str, simple: Optional[str] = "False"):
    """Returns the lyrics of a song. Requires the song name to function properly. Can also add the artist on the end for more accurate results!"""

    async with aiosqlite.connect("./lyrics.db") as db:
        cursor = await db.execute(
            "SELECT * FROM songs WHERE song = ?",
            (song,),
        )
        data = await cursor.fetchall()
        o = data
        notempty = bool(o)
        if data is not None:
            if notempty is True:
                if simple.lower() == "true":
                    return PlainTextResponse(data[0][1])
                return {"success": 1, "data": {"lyrics": data[0][1]}}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://some-random-api.ml/lyrics?title={song}"
        ) as resp:
            if resp.status != 200:
                GENIUS_API_URL = "https://api.genius.com"
                headers = {
                    "Authorization": f"Bearer H-KtNuYpHYXoBJqkt_uScjLamVMBmPOUqinXD2fAS9ictcy2c83ZeeCUHPJticwe"
                }
                params = {"q": song}

                async with session.get(
                    GENIUS_API_URL + "/search", params=params, headers=headers
                ) as resp:
                    if resp.status != 200:
                        return {
                            "success": 0,
                            "data": {
                                "errormessage": "Couldn't fetch the Lyrics!",
                                "backup": "V1",
                            },
                        }
                    data = await resp.json()
                    song_artist = data["response"]["hits"][0]["result"][
                        "primary_artist"
                    ]["name"]
                    # https://api.lyrics.ovh/v1/artist/title
                    async with session.get(
                        f"https://api.lyrics.ovh/v1/{song_artist}/{song}"
                    ) as resp:
                        if resp.status != 200:
                            print(song, "\n", song_artist)
                            return {
                                "success": 0,
                                "data": {
                                    "errormessage": "Couldn't fetch the Lyrics!",
                                    "backup": "V2",
                                },
                            }
                        data = await resp.json()
                        lyrics = data["lyrics"]
            else:
                data = await resp.json()
                lyrics = data["lyrics"]

    async with aiosqlite.connect("./lyrics.db") as db:
        await db.execute(
            "INSERT INTO songs VALUES (?, ?)",
            (song, lyrics),
        )
        await db.commit()

    if simple.lower() == "true":
        return PlainTextResponse(lyrics)
    return {"success": 1, "data": {"lyrics": lyrics}}


@app.get("/coin_value")
async def crypto_info(crypto: str, simple: Optional[str] = "False"):
    """Returns the price of a crypto currency"""
    url = f"https://api.coinpaprika.com/v1/coins/{crypto}"
    do_statistics("coin_value")
    async with aiohttp.ClientSession() as resp:
        async with resp.get(url) as resp:
            data = await resp.json()
            if simple.lower() == "true":
                return PlainTextResponse(
                    f"{data['name']} is worth {data['price_usd']} USD"
                )
            return {"success": 1, "data": {crypto: data}}


@app.get("/waifu")
async def waifu(type: Optional[str] = "waifu"):
    """Returns an image of a waifu. Will return types of Waifus if the type of waifu is invalid. All images are SFW content."""
    waifu_types = [
        "waifu",
        "neko",
        "shinobu",
        "megumin",
        "bully",
        "cuddle",
        "cry",
        "hug",
        "awoo",
        "kiss",
        "lick",
        "pat",
        "smug",
        "bonk",
        "yeet",
        "blush",
        "smile",
        "wave",
        "highfive",
        "handhold",
        "nom",
        "bite",
        "glomp",
        "slap",
        "kill",
        "kick",
        "happy",
        "wink",
        "poke",
        "dance",
        "cringe",
    ]
    if not type in waifu_types:
        return {
            "success": 0,
            "data": {
                "errormessage": "That is not a valid Waifu type!",
                "types": waifu_types,
            },
        }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.waifu.pics/sfw/{type}") as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the Waifu Image!",
                    },
                }
            data = await resp.json()
            url = data["url"]

        async with session.get(url) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {"errormessage": "Couldn't fetch the Waifu Image!"},
                }
            else:
                meme_bytes = await resp.read()
                await do_statistics("waifu")
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")


@app.get("/songinfo")
async def song_info(song: str):
    GENIUS_API_URL = "https://api.genius.com"
    headers = {
        "Authorization": f"Bearer H-KtNuYpHYXoBJqkt_uScjLamVMBmPOUqinXD2fAS9ictcy2c83ZeeCUHPJticwe"
    }
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

        await do_statistics("song_info")
        return data


@app.get("/mcstatus")
async def mcstatus(host: str, port: str = None):
    """Returns the status of a minecraft server"""
    if not port:
        port = 25565
    try:
        server = MinecraftServer.lookup(host + ":" + str(port))
        status = server.status()
    except Exception as e:
        return {
            "success": 0,
            "data": {"errormessage": f"Unexpected error: {e}"},
        }

    await do_statistics("mcstatus")
    return {
        "success": 1,
        "data": {
            "host": host,
            "port": port,
            "online": status.players.online,
            "max": status.players.max,
        },
    }


@app.get("/bored")
async def bored():
    """Returns a bored fact"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.boredapi.com/api/activity") as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the bored fact!",
                    },
                }
            data = await resp.json()

    await do_statistics("bored")
    return {"success": 1, "data": data}


@app.get("/numberfact/{number:int}")
async def numberfact(number):

    """Returns a random number fact"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://numbersapi.com/{number}") as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the number fact!",
                    },
                }
            data = await resp.text()
            if "(submit one to numbersapi at google mail!)" in data:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the number fact!",
                    },
                }

    await do_statistics("numberfact")
    return {"success": 1, "data": data}


@app.get("/randomuser")
async def randomuser():
    """Returns a random user"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://randomuser.me/api/") as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the random user!",
                    },
                }
            data = await resp.json()

    await do_statistics("randomuser")
    return {"success": 1, "data": data["results"][0]}


#! kinda Secret google endpoints


@app.get("/autofill")
async def autofill(query: str):
    # This “API” is a bit of a hack; it was only meant for use by
    # Google’s own products. and hence it is undocumented.
    # Attribution: https://shreyaschand.com/blog/2013/01/03/google-autocomplete-api/
    # I’m not sure if this is the best way to do this, but it works.
    BASE_URL = "https://suggestqueries.google.com/complete/search"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            BASE_URL, params={"client": "firefox", "q": query, "hl": "en"}
        ) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the autofill!",
                    },
                }
            response = await resp.text()
            response = response.split("(")[0].split(")")[0]
            response = json.loads(response)
            data = response[1]
            data = data[:10]

    await do_statistics("autofill")
    return {"success": 1, "data": data}


#!#################################################
# * Image providers and image processing
#!#################################################


@app.get("/dog")
async def dog():
    await do_statistics("dog")

    meme = await get_meme(
        random.choice(["dogpictures", "lookatmydog", "rarepuppers", "Zoomies"])
    )
    async with aiohttp.ClientSession() as resp:
        async with resp.get(meme["url"]) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {"errormessage": "Couldn't fetch the dog!"},
                }
            else:
                meme_bytes = await resp.read()
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")


@app.get("/cat")
async def cat():
    await do_statistics("cat")
    meme = await get_meme("cat")
    async with aiohttp.ClientSession() as resp:
        async with resp.get(meme["url"]) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {"errormessage": "Couldn't fetch the cat!"},
                }
            else:
                meme_bytes = await resp.read()
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")


@app.get("/fox")
async def fox():
    await do_statistics("fox")
    meme = await get_meme("fox")
    async with aiohttp.ClientSession() as resp:
        async with resp.get(meme["url"]) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {"errormessage": "Couldn't fetch the fox!"},
                }
            else:
                meme_bytes = await resp.read()
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")


@app.get("/create_meme")
async def create_meme(top: str, bottom: str, image: str = None):
    if image in ["aliens", "sap", "successkid"]:
        image = f"./data/images/{image}.jpg"
    elif image is None:
        image = "./data/images/successkid.jpg"
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(image) as resp:
                if resp.status != 200:
                    return {
                        "success": 0,
                        "data": {
                            "errormessage": "Couldn't fetch the image!",
                        },
                    }
                image = await resp.read()
                async with aiofiles.open("./data/images/temp.jpg", "wb") as f:
                    await f.write(image)
                image = "./data/images/temp.jpg"
    await do_statistics("create_meme")
    make_meme(top, bottom, image)
    return FileResponse("./temp.png")


@app.get("/mealsome")
async def meme_template_mealsome(me: str, alsome: str):
    args = {alsome, me}
    await do_statistics("mealsome")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("mealsome", args=args)
    return StreamingResponse(meme, media_type="image/png")


@app.get("/itsretarded")
async def meme_template_itsretarded(text: str):
    args = {text}
    await do_statistics("itsretarded")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("itsretarded", args=args)
    return StreamingResponse(meme, media_type="image/png")


@app.get("/headache")
async def meme_template_headache(text: str):
    args = {text}
    await do_statistics("headache")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("headache", args=args)
    return StreamingResponse(meme, media_type="image/png")


@app.get("/classnote")
async def meme_template_classnote(text: str):
    args = {text}
    await do_statistics("itstime")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("classnote", args=args)
    return StreamingResponse(meme, media_type="image/png")


@app.get("/nutbutton")
async def meme_template_nutbutton(text: str):
    args = {text}
    await do_statistics("nutbutton")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("nutbutton", args=args)
    return StreamingResponse(meme, media_type="image/png")


@app.get("/pills")
async def meme_template_pills(text: str):
    args = {text}
    await do_statistics("pills")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("pills", args=args)
    return StreamingResponse(meme, media_type="image/png")


@app.get("/balloon")
async def meme_template_balloon(text: str, person: str, stopper: str):
    args = {text, person, stopper}
    await do_statistics("balloon")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("balloon", args=args)
    return StreamingResponse(meme, media_type="image/png")


#!#################################################
# * Undocumented, for personal use
#!#################################################


@app.get("/stats")
async def stats():
    with open("statistics.json", "r") as f:
        statistics = json.load(f)

    await do_statistics("stats")
    return {"success": 1, "data": {"statistics": statistics}}
