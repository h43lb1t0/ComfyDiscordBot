from datetime import datetime
import os
import random
import sys
import websocket
import uuid
import json
import urllib.request
import urllib.parse
import time
import yaml
from logger import Logger

class ComfyApi():
    
    def read_yml(self, attr: str, value: str):
        with open(self.config_file, 'r') as file:
            config = yaml.safe_load(file)
        
        info = config.get(attr, {}).get(value)
        if info:
            return info
        else:
            raise ValueError(f"{value} not found in the configuration file")
    
    
    def __init__(self):
        self.config_file = "config.yml"
        self.server_address = self.read_yml("server", "address")
        self.client_id = str(uuid.uuid4())
        #self.logger = Logger(self.read_yml("logger", "debug"))

    def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req =  urllib.request.Request("http://{}/prompt".format(self.server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen("http://{}/view?{}".format(self.server_address, url_values)) as response:
            return response.read()

    def get_history(self, prompt_id):
        with urllib.request.urlopen("http://{}/history/{}".format(self.server_address, prompt_id)) as response:
            return json.loads(response.read())

    def get_images(self, ws, prompt):
        prompt_id = self.queue_prompt(prompt)['prompt_id']
        output_images = {}
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break #Execution is done
            else:
                continue #previews are binary data

        history = self.get_history(prompt_id)[prompt_id]
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
        
    
    
    async def generate_images(self, prompt_text,supporting_prompt, dimensions: str, batch_size):

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
        prompt["75"]["inputs"]["text_l"] = supporting_prompt
        prompt["120"]["inputs"]["text"] = prompt["75"]["inputs"]["text_g"]

        # seed
        prompt["22"]["inputs"]["noise_seed"] = random.randint(0, sys.maxsize)

        # batch size
        prompt["5"]["inputs"]["batch_size"] = batch_size



        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(self.server_address, self.client_id))
        return self.get_images(ws, prompt)



    """ for node_id in images:
        date_string = datetime.now().strftime('%Y-%m-%d')
        if not os.path.isdir(date_string):
            os.mkdir(date_string)
        for image_data in images[node_id]:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))
            image.save(f"{date_string}/image-{time.time()}.png") """

