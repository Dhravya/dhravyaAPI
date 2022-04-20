from PIL import Image, ImageFont, ImageDraw
import io

async def make_level_card(
    user_pfp:str,
    username:str,
    discriminator: str,
    server_rank: str,
    level:str,
    exp:str,
    max_exp=None,
    weekly_rank=None,
):
    # Choosing the template based on the stuff we already have
    template_with_weekly = Image.open("./utility/imgen/template_noweekly.png")
    template_without_weekly = Image.open("./utility/imgen/template.png")
    if weekly_rank is None:
        template = template_with_weekly
    else:
        template = template_without_weekly


    # Resizing the user profilepic and making it circle cropped
    user_pfp = Image.open(io.BytesIO(user_pfp))
    user_pfp = user_pfp.resize((94, 94), Image.ANTIALIAS)
    user_pfp = user_pfp.convert("RGBA")
    mask = Image.new("L", user_pfp.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, user_pfp.size[0], user_pfp.size[1]), fill=255)
    user_pfp.putalpha(mask)
    
    template.paste(user_pfp, (58, 64), user_pfp)

    # Adding the username and discriminator
    font = ImageFont.truetype("./data/fonts/ceribri.ttf", size=34)
    draw = ImageDraw.Draw(template)
    draw.text((200, 47), username, (252, 232, 158), font=font)
    print("something")
    # Discriminator
    if not discriminator.startswith("#"):
        discriminator = "#" + discriminator
    font = ImageFont.truetype("./data/fonts/ceribri.ttf", size=30)
    draw = ImageDraw.Draw(template)
    decider = len(username) * 21
    move_image_down = False
    # Some weird shit to make the discriminator fit in the box
    if decider > 400:
        move_image_down = True
    elif decider > 330:
        decider -= 40
    y_coord = 50
    if move_image_down:
        y_coord += 39
        decider = 250
    print(decider)
    draw.text((200 + decider, y_coord), discriminator, (97, 94, 76), font=font)
    template.save("./temp.png")

    # Server rank
    server_font = 30
    if len(str(server_rank)) > 9:
        server_font = 15
    elif len(str(server_rank)) > 5:
        server_font = 20
    font = ImageFont.truetype("./data/fonts/ceribri.ttf", size=server_font)
    draw = ImageDraw.Draw(template)
    server_x_coords = 270
    # Some weird shit to make the server rank fit in the box
    for i in range(len(str(server_rank))):
        if server_x_coords == 230:
            break
        server_x_coords -= 5
    draw.text((server_x_coords, 146), server_rank, (252, 232, 158), font=font)

    # Weekly rank
    if weekly_rank:
        weekly_font = 30
        if len(str(weekly_rank)) > 9:
            weekly_font = 15
        elif len(str(weekly_rank)) > 5:
            weekly_font = 20
        font = ImageFont.truetype("./data/fonts/ceribri.ttf", size=weekly_font)
        draw = ImageDraw.Draw(template)
        draw.text((375, 146), weekly_rank, (255, 255, 255), font=font)

    # Level
    level_x_coord = 740
    # For every length of the level, we need to move the image to the left
    for i in range(len(str(level))):
        level_x_coord -= 5
    font = ImageFont.truetype("./data\fonts\ceribri.ttf", size=20)
    draw = ImageDraw.Draw(template)
    draw.text((level_x_coord, 55), level, (252, 232, 158), font=font)

    # EXP
    exp_x_coord = 740 if max_exp == None else 730
    # For every length of the level, we need to move the image to the left
    for i in range(len(str(exp))):
        exp_x_coord -= 5
    font = ImageFont.truetype("./data\fonts\ceribri.ttf", size=20)
    draw = ImageDraw.Draw(template)
    draw.text((exp_x_coord, 149), exp, (255, 255, 255), font=font)

    # Max EXP
    if max_exp:
        max_exp_x_cord = 740 + len(str(exp)) * 10
        # For every length of the level, we need to move the image to the left
        for i in range(len(str(max_exp))):
            max_exp_x_cord -= 5
        font = ImageFont.truetype("./data/fonts/ceribri.ttf", size=15)
        draw = ImageDraw.Draw(template)
        draw.text((max_exp_x_cord, 153), "/" + max_exp, "#36393f", font=font)

    bytesIO = io.BytesIO()
    template.save(bytesIO, "PNG")
    bytesIO.seek(0)
    return bytesIO
