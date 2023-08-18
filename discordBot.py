import os
import sys
import git
from git import Repo
from pprint import pprint
import interactions
from logger import Logger

logger = Logger()

repo_url = 'https://github.com/twri/sdxl_prompt_styler'
destination_dir = os.path.join(os.curdir,'repositories', "sdxl_prompt_styler")
if not os.path.exists(os.path.join(destination_dir, '.git')):
    print(f"Cloning {repo_url} to {destination_dir}...")
    Repo.clone_from(repo_url, destination_dir)
else:
    print(f"The repository is already cloned at {destination_dir}.")

sys.path.append(destination_dir)

from sdxl_prompt_styler import load_styles_from_directory, read_sdxl_templates_replace_and_combine, read_json_file

combined_data, unique_style_names = load_styles_from_directory(destination_dir)

choices_sai = []
choices_ads = []


for style in unique_style_names:
    if style.startswith("sai"):
        choices_sai.append(interactions.SlashCommandChoice(name=style, value=style))
    else:
        choices_ads.append(interactions.SlashCommandChoice(name=style, value=style))



with open("TOKEN") as token:
    discord_bot_token = token.read()

from core import ComfyApi

api = ComfyApi()
    
bot = interactions.Client(token=discord_bot_token)

logger.log_info("I'm ready!")       

@interactions.slash_command(
    name="create",
    description="This is the first command I made!",
)
@interactions.slash_option(
    name="prompt",
    description="postive prompt",
    required=True,
    opt_type=interactions.OptionType.STRING
)

@interactions.slash_option(
    name="style",
    description="select a style for your images",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=choices_sai
    
)

async def my_first_command(ctx: interactions.SlashContext, prompt : str, style : str):
    text_g, neg_prompt = read_sdxl_templates_replace_and_combine(read_json_file(os.path.join(destination_dir, "sdxl_styles_sai.json")), style, prompt, "")
    await ctx.send(text_g)
    files = []
    try:
        images = api.generate_images(text_g)
    except:
        await ctx.send("I'm sorry, but i had trouble connecting to the ComfyUi API")
        return
    for node_id in images:
        for image_data in images[node_id]:
            import io
            files.append(interactions.File(file=io.BytesIO(image_data), content_type="image", file_name="img.png"))
    await ctx.send(file=files)

bot.start()