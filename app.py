from fastapi import FastAPI
import praw
import random

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
@app.get("/eightball")
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