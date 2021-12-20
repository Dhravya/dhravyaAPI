import random
import dotenv
import os
import json
import requests
import io

import qrcode
from qrcode.image import styles
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import *

import praw
import pytesseract

from flask import Flask, jsonify, render_template, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


from .qr_stuff import *
from .memes import *

dotenv.load_dotenv()

app = Flask(__name__)
types_accepted = ["default", "colour", "color", "pattern"]

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

reddit = praw.Reddit(
    client_id="SwiSNW8bR-yGZ3N0ThTIIw",
    client_secret="v04mt8iI5nuw1D6GzR9Ckg1KI5h0Eg",
    user_agent="Random api lol",
)

limiter = Limiter(
    app, key_func=get_remote_address, default_limits=[
        "8000 per day", "3000 per hour"]
)


@app.route('/')
def index():
    return render_template('index.html')



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
    return jsonify({"response": random.choice(answers)})


@app.route("/qrcode")
@app.route("/qr")
@limiter.limit("20 per minute")
def qrcode_generator():
    query = request.args.get("query")
    if not query:
        return jsonify(
            {
                "error": "No query provided, You need to provide a query to generate a QR code"
            }
        )
    if len(query) > 250 or len(query) < 1:
        return jsonify({"error": "Query must have between 1 and 250 characters."})

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
        return jsonify({"error": "Drawer not found"})
    if mask not in styles["masks"]:
        return jsonify({"error": "Mask not found"})

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
        return jsonify({"error": str(e)})
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
            return jsonify({"error": "Topic not found"})

        # Get a random meme from the subreddit
    else:
        subreddit = reddit.subreddit(random.choice(topics_accepted[topic]))


    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_meme_requests"] + 1
    data["total_meme_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    decider = random.randint(0, 2)
    if decider == 0:
        submission = random.choice(list(subreddit.hot(limit=100)))
    elif decider == 1:
        submission = random.choice(list(subreddit.new(limit=100)))
    else:
        submission = random.choice(list(subreddit.top(limit=100)))
    if not submission:
        return jsonify({"error": "No memes found"})

    return jsonify(
        {
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
@app.route("/ocr", methods=["GET","POST"])
@limiter.limit("15 per minute")
def ocr():

    imagefile = request.args.get("url")
    # Save the image to a file

    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_ocr_requests"] + 1
    data["total_ocr_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    if not imagefile.startswith("http"):
        imagefile = "https://" + imagefile
    if not imagefile:
        return jsonify({"error": "No image provided"})
    if not imagefile.startswith("http") and not imagefile.endswith(".jpg") or not imagefile.endswith(".png"):
        return jsonify({"error": "Only Links with .jpg or .png are accepted"})
    image = requests.get(imagefile)
    img = Image.open(io.BytesIO(image.content))
    # Run the OCR
    text = pytesseract.image_to_string(img)
    # Remove the file\
    return jsonify({"text": text})


@app.route("/compliment")
@app.route("/compliments")
def compliment():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_compliment_requests"] + 1
    data["total_compliment_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    with open("/var/www/api/dhravyaAPI/compliments.txt", "r",encoding="utf-8") as f:
        # Get a random compliment
        compliments = f.readlines()

        return jsonify({"compliment": compliments[random.randrange(0, len(compliments))][:-2] })

@app.route("/wyr")
@app.route("/wouldyourather")
def wyr():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_wyr_requests"] + 1
    data["total_wyr_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    with open("/var/www/api/dhravyaAPI/wyr.txt", "r",encoding="utf-8") as f:
        # Get a random compliment
        wyr = f.readlines()

        return jsonify({"wyr": wyr[random.randrange(0, len(wyr))][:-2] })

@app.route("/joke")
@app.route("/jokes")
def joke():
    with open("/var/www/api/dhravyaAPI/data.json", "r") as f:
        data = json.load(f)
    f = data["total_joke_requests"] + 1
    data["total_joke_requests"] = f
    with open("/var/www/api/dhravyaAPI/data.json", "w") as f:
        json.dump(data, f)

    with open("/var/www/api/dhravyaAPI/jokes.txt", "r",encoding="utf-8") as f:
        # Get a random compliment
        jokes = f.readlines()

        return jsonify({"joke": jokes[random.randrange(0, len(jokes))][:-2] })



if __name__ == "__main__":
    app.run(port=80)
