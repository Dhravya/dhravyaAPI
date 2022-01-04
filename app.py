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
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse, PlainTextResponse

from mcstatus import MinecraftServer
import pyfiglet
import qrcode
from qrcode.image.styledpil import StyledPilImage
import MemePy

from extras.qr_stuff import _styles
from extras.meme_fetcher import get_meme, topics_accepted
from extras.memegenerator import make_meme
from extras.do_stats import do_statistics

# Defining apps and configs.
app = FastAPI()

FIGLET_FONTS = """3-d, 3x5, 5lineoblique, alphabet, banner3-D, 
                    doh, isometric1, letters, alligator, dotmatrix, 
                    bubble, bulbhead, digital"""

#!#################################################
# * Unimportant stuff, testing, etc
#!#################################################


@app.get("/")
async def test():
    return RedirectResponse("/docs")


@app.get("/8ball")
async def eightball(simple: str = None):

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
    
    if simple == "true":
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
# * Joke, WYR, etc generators
#!#################################################


@app.get("/wyr")
async def wyr(simple: str = None):
    """Returns a would you rather question"""
    async with aiofiles.open("./data/txt/wyr.txt", "r") as f:
        data = await f.readlines()
    question = data[random.randrange(0, len(data))][:-2].split(" or ")

    await do_statistics("wyr")
    if simple == "true":
        question[0] = question[0].capitalize()
        question[1] = question[1].capitalize()
        e = f"{question[0]} or {question[1]}?"
        return PlainTextResponse(e)
    return {"success": 1, "data": {"Would you rather": question}}


@app.get("/joke")
async def joke(simple: str = None):
    """Returns a joke"""
    async with aiofiles.open("./data/txt/jokes.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    joke = data[random.randrange(0, len(data))][:-2]

    await do_statistics("joke")
    if simple == "true":
        return PlainTextResponse(joke)
    return {"success": 1, "data": {"Joke": joke}}


@app.get("/compliment")
async def compliment(simple: str = None):
    """Returns a compliment"""
    async with aiofiles.open("./data/txt/compliments.txt", "r") as f:
        data = await f.readlines()
    compliment = data[random.randrange(0, len(data))][:-2]

    await do_statistics("compliment")
    if simple == "true":
        return PlainTextResponse(compliment)
    return {"success": 1, "data": {"Compliment": compliment}}


@app.get("/topic")
async def topic(simple: str = None):
    """Returns a topic"""
    async with aiofiles.open("./data/txt/topics.txt", "r", encoding="utf8") as f:
        data = await f.readlines()
    topic = data[random.randrange(0, len(data))][:-2]

    await do_statistics("topic")
    if simple == "true":
        e = f"{topic}?"
        return PlainTextResponse(e)
    return {"success": 1, "data": {"Topic": topic}}


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


@app.get("/songinfo")
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
    pass


@app.get("/cat")
async def cat():
    await do_statistics("cat")
    pass

@app.get("/create_meme")
async def create_meme(top: str, bottom: str, image: str= None):
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
    args = { alsome, me}
    await do_statistics("mealsome")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("mealsome",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/itsretarded")
async def meme_template_itsretarded(text: str):
    args = { text}
    await do_statistics("itsretarded")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("itsretarded",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/headache")
async def meme_template_headache(text: str):
    args = { text}
    await do_statistics("headache")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("headache",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/classnote")
async def meme_template_classnote(text: str):
    args = { text}
    await do_statistics("itstime")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("classnote",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/nutbutton")
async def meme_template_nutbutton(text: str):
    args = { text}
    await do_statistics("nutbutton")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("nutbutton",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/pills")
async def meme_template_pills(text:str):
    args = {text}
    await do_statistics("pills")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("pills",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/balloon")
async def meme_template_balloon(text:str, person:str, stopper:str):
    args = {text, person, stopper}
    await do_statistics("balloon")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("balloon",args=args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/classy")
async def meme_template_classy(upper:str, lower:str):
    args = {upper, lower}
    await do_statistics("classy")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("classy",args)
    return StreamingResponse(meme, media_type="image/png")

@app.get("/finally")
async def meme_template_finally(text:str):
    args = {text}
    await do_statistics("finally")
    meme = MemePy.MemeGenerator.get_meme_image_bytes("finally",args)
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
