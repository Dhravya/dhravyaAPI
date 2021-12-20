# Dhravya API Endpoints

  - [/8ball (GET) {/eightball} - Get a random answer](#8ball-get-eightball---get-a-random-answer)
  - [/qrcode (GET) {/qr} - Get a QR code](#qrcode-get-qr---get-a-qr-code)
  - [/meme (GET) {/memes} - Gets a random meme from reddit](#meme-get-memes---gets-a-random-meme-from-reddit)
  - [/meme/<Topic> (GET) {/memes/<topic>} - Gets a meme according to your query](#memetopic-get-memestopic---gets-a-meme-according-to-your-query)
  - [/ocr (GET) - Get the text from an image](#ocr-get---get-the-text-from-an-image)
  - [/compliment (GET) {/compliments} - Get a compliment](#compliment-get-compliments---get-a-compliment)
  - [/wyr (GET) {/wouldyourather} - Get a would you rather question](#wyr-get-wouldyourather---get-a-would-you-rather-question)
  - [/joke (GET) {/jokes} - Gets a random joke](#joke-get-jokes---gets-a-random-joke)
  - [Currently accepted colours:](#currently-accepted-colours)


### /8ball (GET) {/eightball} - Get a random answer
Params: `None`

### /qrcode (GET) {/qr} - Get a QR code
Params:
- `query`: The text to encode - Should be less than 250 characters
- `drawer` : The style of the qr code. This must be a number between 1 and 6
  - 1: Square Module (Default)
  - 2: Gapped Squares
  - 3: Circles Module
  - 4: Rounded Module
  - 5: Vertical Bars
  - 6: Horizontal Bars
- `mask` : The mask for qr code This must be a number between 1 and 5
  - 1: Solid fill (Default)
  - 2: Radial Gradient
  - 3: Square Gradient
  - 4: Horizontal Gradient
  - 5: Vertical Gradient
- `fg` : The foreground colour for qr code, Should be a colour which is in accepted list at the end of the page
- `bg`: The background colour for qr code, Should be a colour which is in accepted list at the end of the page

> QR code returns: A PNG image of the qr code

### /meme (GET) {/memes} - Gets a random meme from reddit
Params: `subreddit` - Choose a subreddit to get memes from (Instead of using the default)
Current sources of random memes are:
- [r/memes](https://www.reddit.com/r/memes/)
- [r/meme](https://www.reddit.com/r/meme/)
- [r/dankmemes](https://www.reddit.com/r/dankmemes/)
- [r/funny](https://www.reddit.com/r/funny/)
> Meme returns: A PNG, JPEG, JPG, or a GIF image of a meme.

### /meme/<Topic> (GET) {/memes/<topic>} - Gets a meme according to your query
Pre-Listed topics (For subreddits):
```json
{
"random" : ["memes","meme","dankmemes"],
"memes" : ["memes"],
"coding" : ["programmerhumor","programmingmemes","programminghumor","codingmemes","pythonmemes","javascriptmemes"]
}
```

> Pre listed topics means that these endpoints automatically choose from these "hot" subreddits for you, instead of searching for a relevant subreddit.

> Returns: A response with the information about the meme on reddit, as a `json`

### /ocr (GET) - Get the text from an image
Params:
- `url` : The url of the image to get the text from

> Returns: A response with the text from the image as a JSON

### /compliment (GET) {/compliments} - Get a compliment
Params: `None`
> Returns: A compliment as a JSON response

### /wyr (GET) {/wouldyourather} - Get a would you rather question
Params: `None`
> Returns: A would you rather question as a JSON response

### /joke (GET) {/jokes} - Gets a random joke
Params: `None`
> Returns: A random joke as a JSON response


### Currently accepted colours:
- Random
- Red
- Black
- White
- Green 
- Yellow
- Cyan
- Blue
- Magenta
- Gray
- Orange
- Purple
- Brown
- Pink
- Lime
- Olive
