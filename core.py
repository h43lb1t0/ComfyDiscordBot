from pprint import pprint
import random
import sys
import aiohttp
import urllib.parse
import uuid
import json
import websockets
import yaml
from logger import Logger


class ComfyApi():
    
    def read_yml(self, attr: str, value: str):
        with open(self.config_file, 'r') as file:
            config = yaml.safe_load(file.read())
        
        info = config.get(attr, {}).get(value)
        if info:
            return info
        else:
            raise ValueError(f"{value} not found in the configuration file")

    def __init__(self):
        self.config_file = "config.yml"
        self.server_address = self.read_yml("server", "address")
        port = self.read_yml("server", "port")
        self.server_address = f"{self.server_address}:{port}"
        self.client_id = str(uuid.uuid4())
        
    async def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        url = f"http://{self.server_address}/prompt"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                return await resp.json()
    
    async def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        url = f"http://{self.server_address}/view?{url_values}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.read()

    async def get_history(self, prompt_id):
        url = f"http://{self.server_address}/history/{prompt_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def get_images(self, ws, prompt):
        result = await self.queue_prompt(prompt)
        prompt_id = result['prompt_id']

        output_images = {}
        # ... (The rest remains largely the same, except that it will use await for async methods

        while True:
            out = await ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break #Execution is done
            else:
                continue #previews are binary data

        history = await self.get_history(prompt_id)
        history = history[prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    images_output = []
                    for image in node_output['images']:
                        image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                        images_output.append(image_data)
                output_images[node_id] = images_output

        return output_images
    
    def parse_dimensions(self, dimensions: str):
        print(dimensions)
        try:
            width, height = map(int, dimensions.split('x'))
            return width, height
        except ValueError:
            raise ValueError(f"Invalid format for dimensions: {dimensions}")
        
    
    
    async def generate_images(self, prompt_text,supporting_prompt, dimensions: str, batch_size, nsfw : bool = False):

        if nsfw:
            with open("workflow_nsfw.json", "r") as file:
                json_content = file.read()
        else:
            with open("workflow.json", "r") as file:
                json_content = file.read()
        

        prompt = json.loads(json_content)

        try:
            width, height = self.parse_dimensions(dimensions)
        except Exception as e:
            print(e)

        # image dimensions
        prompt["5"]["inputs"]["width"] = width
        prompt["5"]["inputs"]["height"] = height

        # prompt
        prompt["75"]["inputs"]["text_g"] = prompt_text # base
        prompt["75"]["inputs"]["text_l"] += supporting_prompt
        prompt["120"]["inputs"]["text"] = prompt["75"]["inputs"]["text_g"]

        # seed
        prompt["22"]["inputs"]["noise_seed"] = random.randint(0, sys.maxsize)
        #prompt["22"]["inputs"]["noise_seed"] = 1 # for debugging

        # batch size
        prompt["5"]["inputs"]["batch_size"] = batch_size


        async with websockets.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}") as ws:
            files = await self.get_images(ws, prompt)
            return files
        

    async def upscaled_images(self, filename):
        with open("workflow_upscale.json", "r") as file:
                json_content = file.read()

        prompt = json.loads(json_content)

        prompt["1"]["inputs"]["image"] += filename

        async with websockets.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}") as ws:
            files = await self.get_images(ws, prompt)
            return files
        
        





