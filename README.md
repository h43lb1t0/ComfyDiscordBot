# ComfyDiscordBot
a discord bot for stable difiusion [ComfyUI](https://github.com/comfyanonymous/ComfyUI) with some inpiration from the [Foocus UI](https://github.com/lllyasviel/Fooocus). simply wirte your prompt, choose on of the styles you like and wait for however long your GPU needs.

<hr>

## installation

1. Install ComfyUI and Download the SDXL base and refiner models.
2. config your model path in the `config.yml` file.
3. clone this repo
```bash
git clone https://github.com/h43lb1t0/ComfyDiscordBot
cd ComfyDiscordBot
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirments.txt
python3 discordBot.py
```

## usages
1. go to https://discord.com/developers/applications and create a new Bot. Follow [this](https://interactionspy.readthedocs.io/en/latest/quickstart.html) instructions. 
2. put your discord bot token in a file `TOKEN` in the rrot of this repo. KEEP IT SECRET!
3. have fun!
