import asyncio
import os
import sys
from git import Repo
import interactions
from logger import Logger
from dotenv import load_dotenv
from ssh import ShhHelper



logger = Logger()

repo_url = 'https://github.com/twri/sdxl_prompt_styler'
destination_dir = os.path.join(os.curdir,'repositories', "sdxl_prompt_styler")
if not os.path.exists(os.path.join(destination_dir, '.git')):
    print(f"Cloning {repo_url} to {destination_dir}...")
    Repo.clone_from(repo_url, destination_dir)
else:
    print(f"The repository is already cloned at {destination_dir}.")
    print("Pulling latest changes...")
    repo = Repo(destination_dir)
    origin = repo.remotes.origin
    origin.pull()

sys.path.append(destination_dir)

from sdxl_prompt_styler import load_styles_from_directory, read_sdxl_templates_replace_and_combine, read_json_file

combined_data, unique_style_names = load_styles_from_directory(destination_dir)

choices_sai = []
choices_ads = []


for style in unique_style_names:
    if style.startswith("sai"):
        choices_sai.append(interactions.SlashCommandChoice(name=style.replace("sai-",""), value=style))
    else:
        choices_ads.append(interactions.SlashCommandChoice(name=style, value=style))

load_dotenv()

discord_bot_token = os.getenv("discordToken")



from core import ComfyApi

api = ComfyApi()
ssh = ShhHelper(api)
    
bot = interactions.Client(token=discord_bot_token,
                          send_not_ready_messages=True)

logger.log_info("I'm ready!")      

demensions = [
    interactions.SlashCommandChoice(name="1024x1024", value="1024x1024"),
    interactions.SlashCommandChoice(name="896x1152", value="896x1152"),
    interactions.SlashCommandChoice(name="1152x896", value="1152x896"),
    interactions.SlashCommandChoice(name="960x1024", value="960x1024"),
    interactions.SlashCommandChoice(name="1024x960", value="1024x960"),
    interactions.SlashCommandChoice(name="768x1024", value="768x1024")    
    ] 
batch_sizes = [
    interactions.SlashCommandChoice(name="1", value=1),
    interactions.SlashCommandChoice(name="2", value=2),
    interactions.SlashCommandChoice(name="3", value=4),
    interactions.SlashCommandChoice(name="4", value=4) 
    ] 

from interactions import ActionRow, Button
from interactions.api.events import Component

image_names = []

@interactions.listen()
async def on_component(event: Component):
    ctx = event.ctx

    match ctx.custom_id:
        case "1":
            await ctx.send("You clicked 1!")
        case "2":
            await ctx.send("You clicked 2!")


from asyncio import Queue

task_queue = Queue()

async def worker():
    
    while True:
        if not task_queue.empty():
            text_g, supporting_prompt, dimensions, batch_size, nsfw, thread_name, thread, autor_mention = await task_queue.get()

            try:
                images = await api.generate_images(text_g, supporting_prompt, dimensions, batch_size, nsfw)
            except Exception as e:
                await thread.send(f"{autor_mention} sorry I can't reach the Comfy API. Try again or (re)start Comfy\nError: {e}")
                continue

            files = []
            if images:
                for node_id in images:
                    print(images)
                    for image_data in images[node_id]:
                        import io
                        img_data = await image_data
                        files.append(interactions.File(file=io.BytesIO(img_data), content_type="image", file_name="img.png"))
                        #image_names.append(img_data['filename'])

                await thread.send(file=files)

                print(image_names)
                """ url = foo.attachments[0].url
                print(url) """

                """ components: list[ActionRow] = [
                    ActionRow(
                        Button(
                            style=interactions.ButtonStyle.GREEN,
                            label="Click Me",
                            custom_id="1"
                        ),
                        Button(
                            style=interactions.ButtonStyle.GREEN,
                            label="Click Me Too",
                            custom_id="2"
                        )
                    )
                ] """

                #await thread.send(f"{autor_mention} your images are ready!", components=components)
                await thread.send(f"{autor_mention} your images are ready!")

                
                print("Files sent.")


                """ var = interactions.EmbedAttachment(files[0])
                foo = interactions.Embed(title="Your images are ready!", description=f"{autor_mention} your images are ready!", color=0x00ff00)

                await thread.send(embed=foo) """
        await asyncio.sleep(1)


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
    name="style",
    description="select a style for your images",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=choices_sai  
)
@interactions.slash_option(
    name="supporting_prompt",
    description="prompt to support the postive prompt",
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name="dimensions",
    description="width, height",
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
    choices=batch_sizes
)
 # Global counter to keep track of API calls
async def create_command(ctx: interactions.SlashContext, prompt : str, style : str, supporting_prompt: str = "", dimensions : str = "1024x1024", batch_size : int = 4, nsfw : bool = False):

    print("create_command")
    await ctx.defer()

    text_g, neg_prompt = read_sdxl_templates_replace_and_combine(read_json_file(os.path.join(destination_dir, "sdxl_styles_sai.json")), style, prompt, "")
    msg = await ctx.send(text_g)

                                 
                                 

    thread_name = f"{ctx.author}"
    thread = await msg.create_thread(thread_name)

    autor_mention = ctx.author.mention

    await thread.send(f"You are at position {task_queue.qsize()} in the queue.\nOne queue position is about 30 seconds up to 2 minutes.")


    await task_queue.put((text_g, supporting_prompt, dimensions, batch_size, nsfw, thread_name, thread, autor_mention))


    """ images, thread_name = await api.generate_images(text_g, supporting_prompt, dimensions, batch_size, nsfw, thread_name)

    print(f"images for thread {thread_name}")


    files = []
    if images:
        for node_id in images:
            for image_data in images[node_id]:
                import io
                files.append(interactions.File(file=io.BytesIO(await image_data), content_type="image", file_name="img.png"))
        await thread.send(file=files)
        print("Files sent.") """



from interactions import listen
from interactions.api.events import Startup
@listen(Startup)
async def onStartup():
    asyncio.create_task(worker())


@interactions.slash_command(
    name="create_nsfw",
    description="create NSFW images with SDXL",
    nsfw=True
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
@interactions.slash_option(
    name="supporting_prompt",
    description="prompt to support the postive prompt",
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name="dimensions",
    description="width, height",
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
    choices=batch_sizes
)
async def nsfw_command(ctx: interactions.SlashContext, prompt : str, style : str, supporting_prompt: str = "", dimensions : str = "1024x1024", batch_size : int = 4):
    await create_command(ctx, prompt, style, supporting_prompt, dimensions, batch_size, nsfw=True)


@interactions.slash_command(name="start",
                            description="start the Comfy API")
async def start_command(ctx: interactions.SlashContext):
    await ctx.defer()
    await ctx.send("Starting Comfy API...")
    started = await ssh.start_server()
    if started:
        await ctx.send("Comfy API started.")
    else:
        await ctx.send("Comfy API failed to start.")

@interactions.slash_command(name="stop",
                            description="stop the Comfy API")
async def stop_command(ctx: interactions.SlashContext):
    await ctx.defer()
    await ctx.send("Stopping Comfy API...")
    started = await ssh.stop_server()
    if started == "stopped":
        await ctx.send("Comfy API stopped.")
    elif started == "not stopped":
        await ctx.send("Comfy API failed to start.")
    else:
        await ctx.send("Comfy API wasn't running.")

@interactions.slash_command(name="status",
                            description="get the status of the Comfy API")
async def status_command(ctx: interactions.SlashContext):
    await ctx.defer()
    await ctx.send("Checking Comfy API status...")
    started = await ssh.try_connect()
    if started:
        await ctx.send("Comfy API is running.")
    else:
        await ctx.send("Comfy API is not running.")

bot.start()

