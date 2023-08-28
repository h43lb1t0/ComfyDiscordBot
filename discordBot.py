import asyncio
import os
import sys
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

demensions = [
    interactions.SlashCommandChoice(name="1024x1024", value="1024x1024"),
    interactions.SlashCommandChoice(name="896x1152", value="768x1024"),
    interactions.SlashCommandChoice(name="1152x896", value="768x1024"),
    interactions.SlashCommandChoice(name="960x1024", value="960x1024"),
    interactions.SlashCommandChoice(name="1024x960", value="1024x960"),
    interactions.SlashCommandChoice(name="768x1024", value="768x1024")    
    ] 




@interactions.slash_command(
    name="create",
    description="create images with SDXL",
)
@interactions.slash_option(
    name="prompt",
    description="postive prompt",
    required=True,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name="supporting_prompt",
    description="prompt to support the postive prompt",
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name="style",
    description="select a style for your images",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=choices_sai  
)
@interactions.slash_option(
    name="dimensions",
    description="demensions for the image",
    required=False,
    opt_type=interactions.OptionType.STRING,
    choices=demensions
)
@interactions.slash_option(
    name="batch_size",
    description="amount of images to generate",
    required=False,
    opt_type=interactions.OptionType.INTEGER,
    min_value=1,
    max_value=4,
    choices=[1, 2, 3, 4]
)

async def my_first_command(ctx: interactions.SlashContext, prompt : str, supporting_prompt: str, style : str, dimensions : str = "1024x1024", batch_size : int = 4):
    text_g, neg_prompt = read_sdxl_templates_replace_and_combine(read_json_file(os.path.join(destination_dir, "sdxl_styles_sai.json")), style, prompt, "")
    msg = await ctx.send(text_g)
    thread = await msg.create_thread(f"Pictures {ctx.author}")
    files = []
    try:
        images = api.generate_images(text_g, supporting_prompt, dimensions, batch_size)
    except Exception as e:
        await ctx.send(f"I'm sorry, but i had trouble connecting to the ComfyUi API\n{e}")
        return
    for node_id in images:
        for image_data in images[node_id]:
            import io
            files.append(interactions.File(file=io.BytesIO(image_data), content_type="image", file_name="img.png"))
    #await ctx.send()
    await thread.send(file=files)
bot.start()
