import json
from typing import Optional
import aiofiles
import aiohttp
import random
import io

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
import praw

import qrcode
from qrcode.image import styles
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import *

from extras.qr_stuff import styles
from extras.meme_fetcher import get_meme, topics_accepted

# Defining apps and configs.
app = FastAPI()
reddit = praw.Reddit(
    client_id="SwiSNW8bR-yGZ3N0ThTIIw",
    client_secret="v04mt8iI5nuw1D6GzR9Ckg1KI5h0Eg",
    user_agent="Random api lol",
)


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
    return {
        "success": 1,
        "data": {
            "answer": random.choice(answers)
        }
    }

@app.get("/qrcode")
async def qr_code(query: Optional[str] = None, drawer: Optional[str] = "1", mask: Optional[str] = "1"):

    if not query:
        return {
            "success": 0,
            "data": {
                "errormessage": "You didn't give a query!"
            }
        }

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
    if drawer not in styles["drawers"]:
        return {
            "success": 0,
            "data": {
                "errormessage": "That drawer is invalid!"
            }
        }
    if mask not in styles["masks"]:
        return {
            "success": 0,
            "data": {
                "errormessage": "That mask is invalid!!"
            }
        }

    fg_color = "black"

    bg_color = "white"

    drawer = styles["drawers"][str(drawer)]
    try:
        if fg_color and bg_color:
            img = qr.make_image(
                fill_color=fg_color, back_color=bg_color, mask=styles["masks"]["1"]
            )
        elif fg_color:
            img = qr.make_image(fill_color=fg_color, mask=mask)
        else:
            img = qr.make_image(
                module_drawer=drawer,
                color_mask=styles["masks"][str(mask)],
                image_factory=StyledPilImage,
                fill_color=fg_color,
                back_color=bg_color,
            )
    except Exception as e:
        return {
            "success": 0,
            "data": {
                "errormessage": f"Unexpected error: {e}"
            }
        }
    img.save(f"./qr_codes/{n}.png", "PNG")
    return FileResponse(f"./qr_codes/{n}.png")


@app.get("/stats")
async def stats():
    with open("statistics.json", "r") as f:
        statistics = json.load(f)
    return {
        "success": 1,
        "data": {
            "statistics": statistics
        }
    }

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
            "selftext" : meme["selftext"],
            "is_nsfw": meme["over_18"]
        }
    }

@app.get("/meme")
async def meme():
    meme = await get_meme("random")

    async with aiohttp.ClientSession() as resp:
        async with resp.get(meme["url"]) as resp:
            if resp.status != 200:
                return {
                    "success": 0,
                    "data": {
                        "errormessage": "Couldn't fetch the meme!"
                    }
                }
            else:
                meme_bytes = await resp.read()
                return StreamingResponse(io.BytesIO(meme_bytes), media_type="image/png")