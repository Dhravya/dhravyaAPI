import random
import dotenv
import os
import json
import requests
import io
import json

import qrcode
from qrcode.image import styles
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import *

import praw
import prawcore
import pytesseract
from mcstatus import MinecraftServer
import pyfiglet

from flask import Flask, jsonify, render_template, request, send_file, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


from .ext.qr_stuff import *
from .ext.memes import *

dotenv.load_dotenv()

app = Flask(__name__)
TYPES_ACCEPTED = ["default", "colour", "color", "pattern"]

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

reddit = praw.Reddit(
    client_id="SwiSNW8bR-yGZ3N0ThTIIw",
    client_secret="v04mt8iI5nuw1D6GzR9Ckg1KI5h0Eg",
    user_agent="Random api lol",
)

limiter = Limiter(
    app, key_func=get_remote_address, default_limits=["1000 per day", "500 per hour"]
)

def jsonify(indent=4, sort_keys=False, **kwargs):
    response = make_response(
        json.dumps(dict(**kwargs), indent=indent, sort_keys=sort_keys)
    )
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["mimetype"] = "application/json"
    response.status_code = 200
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/8ball")
@app.route("/eightball")
@limiter.exempt
def eightball():
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
    return jsonify(**{"response": random.choice(answers)})


@app.route("/qrcode")
@app.route("/qr")
@limiter.limit("20 per minute")
def qrcode_generator():
    query = request.args.get("query")
    if not query:
        return jsonify(
            **{
                "error": "No query provided, You need to provide a query to generate a QR code"
            }
        )
    # if len(query) > 250 or len(query) < 1:
    #     return jsonify(**{"error": "Query must have between 1 and 250 characters."})

    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_qr_requests"] + 1
    data["total_qr_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    n = random.randint(1, 5)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(query)
    qr.make(fit=True)

    drawer = request.args.get("drawer")
    if not drawer:
        drawer = "1"

    mask = request.args.get("mask")
    if not mask:
        mask = "1"

    # CHecks if the drawer and mask is valid
    if drawer not in styles["drawers"]:
        return jsonify(**{"error": "Drawer not found"})
    if mask not in styles["masks"]:
        return jsonify(**{"error": "Mask not found"})

    fg_color = request.args.get("fg")
    if fg_color:
        fg_color = "black"

    bg_color = request.args.get("bg")
    if bg_color:
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
        return jsonify(**{"error": str(e)})
    img.save(f"/var/www/api/dhravyaAPI/qr_codes/{n}.png", "PNG")
    return send_file(f"/var/www/api/dhravyaAPI/qr_codes/{n}.png", mimetype="image/png")


@app.route("/meme")
@app.route("/memes")
def send_single_meme():

    if request.args.get("subreddit"):
        subrddit = request.args.get("subreddit")
    else:
        subreddits = ["memes", "dankmemes", "meme", "funny"]
        subrddit = random.choice(subreddits)
    subreddit = reddit.subreddit(subrddit)

    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_meme_requests"] + 1
    data["total_meme_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    def get_submission(subreddit):
        decider = random.randint(0, 2)
        if decider == 0:
            submission = random.choice(list(subreddit.random_rising()))
        elif decider == 1:
            submission = subreddit.random()
        else:
            submission = random.choice(list(subreddit.hot()))

        return submission

    submission = get_submission(subreddit)

    def generate():
        r = requests.get(submission.url, stream=True)
        for chunk in r.iter_content(2048):
            yield chunk

    return app.response_class(generate(), mimetype="image/jpg")


@app.route("/meme/<topic>")
@app.route("/memes/<topic>")
@limiter.limit("30 per minute")
def memes(topic):
    # Get a meme of the requested topic
    if not topic in topics_accepted:
        topic = topic + "memes"
        # Search for topic using the reddit api
        subreddit = reddit.subreddit(topic)
        if not subreddit:
            return jsonify(**{"error": "Topic not found"})

        # Get a random meme from the subreddit
    else:
        subreddit = reddit.subreddit(random.choice(topics_accepted[topic]))

    if subreddit is None:
        return jsonify({"error": "Topic not found"})

    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_meme_requests"] + 1
    data["total_meme_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    decider = random.randint(0, 2)
    try:
        if decider == 0:
            submission = random.choice(list(subreddit.hot(limit=100)))
        elif decider == 1:
            submission = random.choice(list(subreddit.new(limit=100)))
        else:
            submission = random.choice(list(subreddit.top(limit=100)))
        if not submission:
            return jsonify(**{"error": "No memes found"})
    except prawcore.exceptions.NotFound:
        return jsonify(**{"error": "Topic not found"})

    return jsonify(
        **{
            "url": submission.url,
            "title": submission.title,
            "subreddit": submission.subreddit.display_name,
            "score": submission.score,
            "id": submission.id,
            "nsfw": submission.over_18,
            "selftext": submission.selftext,
            "author": submission.author.name,
            "created": submission.created,
            "permalink": submission.permalink,
        }
    )


# Accept an image from user
@app.route("/ocr", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def ocr():

    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_ocr_requests"] + 1
    data["total_ocr_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    if request.method == "POST":
        # Get the image from the request
        image = request.files["image"]
        # Check if the image is valid
        if not image:
            return jsonify({"error": "No image found"})
        img = Image.open(image)

    elif request.method == "GET":
        imagefile = request.args.get("url")
        # Save the image to a file

        if not imagefile.startswith("http"):
            imagefile = "https://" + imagefile
        if not imagefile:
            return jsonify({"error": "No image provided"})
        image = requests.get(imagefile)
        img = Image.open(io.BytesIO(image.content))
    # Run the OCR
    text = pytesseract.image_to_string(img)
    # Remove the file\
    return jsonify(**{"text": text})


@app.route("/compliment")
@app.route("/compliments")
def compliment():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_compliment_requests"] + 1
    data["total_compliment_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    with open("/var/www/api/dhravyaAPI/txt_files/compliments.txt", "r", encoding="utf-8") as f:
        # Get a random compliment
        compliments = f.readlines()

        return jsonify(
            **{"compliment": compliments[random.randrange(0, len(compliments))][:-2]}
        )


@app.route("/wyr")
@app.route("/wouldyourather")
def wyr():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_wyr_requests"] + 1
    data["total_wyr_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    with open("/var/www/api/dhravyaAPI/txt_files/wyr.txt", "r", encoding="utf-8") as f:
        # Get a random compliment
        wyr = f.readlines()

        return jsonify(**{"wyr": wyr[random.randrange(0, len(wyr))][:-2]})


@app.route("/joke")
@app.route("/jokes")
def joke():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_joke_requests"] + 1
    data["total_joke_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    with open("/var/www/api/dhravyaAPI/txt_files/jokes.txt", "r", encoding="utf-8") as f:
        # Get a random compliment
        jokes = f.readlines()

        return jsonify(**{"joke": jokes[random.randrange(0, len(jokes))][:-2]})


@app.route("/stats")
def stats():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    return jsonify(**data)

@app.route("/ascii")
@app.route("/asciiart")
def ascii():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_ascii_requests"] + 1
    data["total_ascii_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    if not request.args.get("text"):
        return jsonify(**{"error": "No text provided"})

    if not request.args.get("font"):
        result = pyfiglet.figlet_format(request.args.get("text"))
    else:
        try:
            result = pyfiglet.figlet_format(request.args.get("text"), font=request.args.get("font"))
        except:
            return jsonify(**{"error": "Font not found. Accepted fonts are slant, 3-d, 3x5, 5lineoblique, alphabet, banner3-D, doh, isometric1, letters, alligator, dotmatrix, bubble, bulbhead, digital."})
    print(result)
    return jsonify(**{"ascii": result, "font": "Available fonts are: slant, 3-d, 3x5, 5lineoblique, alphabet, banner3-D, doh, isometric1, letters, alligator, dotmatrix, bubble, bulbhead, digital."})

@app.route("/song_info")
def song_info():
    song = request.args.get("song")
    base_url = "http://api.genius.com"
    headers = {'Authorization': 'Bearer H-KtNuYpHYXoBJqkt_uScjLamVMBmPOUqinXD2fAS9ictcy2c83ZeeCUHPJticwe'}

    search_url = base_url + "/search"
    song_title = song
    params = {'q': song_title}
    response = requests.get(search_url, params=params, headers=headers)
    json = response.json()
    return jsonify(**json)

@app.route("/mcstatus")
def mcstatus():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_mcstatus_requests"] + 1
    data["total_mcstatus_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    host = request.args.get("host")
    if not host:
        return jsonify(**{"error": "No host provided"})
    port = request.args.get("port")
    if not port:
        port = 25565

    try:
        server = MinecraftServer.lookup(host + ":" + str(port))
        status = server.status()
    except Exception as e:
        return jsonify(**{"error": "Server not found: " + host + ":" + str(port), "error": str(e)})


    return jsonify(
    **{
        "online": status.players.online,
        "max": status.players.max,
        "latency": str(status.latency) + "ms"
    }
    )

@app.route("/dog")
@app.route("/dogs")
def dog():
    # Get a random dog from /dogs folder
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_dog_requests"] + 1
    data["total_dog_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    dogs = os.listdir("/var/www/api/dhravyaAPI/dogs")
    return send_file("/var/www/api/dhravyaAPI/dogs/" + dogs[random.randrange(0, len(dogs))])

if __name__ == "__main__":
    app.run(port=80)
