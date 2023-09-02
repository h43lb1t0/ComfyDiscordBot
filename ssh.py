import os
import time
import paramiko
from dotenv import load_dotenv
from core import ComfyApi
from aiohttp import ClientSession

class ShhHelper():

    def __init__(self, api):
        self.config_file = "config.yml"
        self.server_address = ComfyApi.read_yml(api, "server", "address")
        self.port = ComfyApi.read_yml(api, "server", "port")
        load_dotenv()
        self.username = os.getenv("comfyServerUsername")
        self.rsa_key_path = os.getenv("sshKeyPath")
        self.private_key = paramiko.RSAKey(filename=self.rsa_key_path)


    async def try_connect(self):
        # this will not work if the comfy server and the discord bot run on the same machine
        async with ClientSession() as session:
            try:
                async with session.get(f"http://{self.server_address}:{self.port}") as response:
                    if response.status == 200:
                        #print("Server started successfully")
                        return True
                    else:
                        #print("Server failed to start")
                        return False
            except Exception as e:
                print(f"Server failed to start\n{e}")
                return False
        

    async def start_server(self):
        # Load your private key
        

        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the server using key-based authentication
            client.connect(hostname=self.server_address, username=self.username, pkey=self.private_key)

            stdin, stdout, stderr = client.exec_command('nohup /media/haelbito/Server_1/stable_difiusion/ComfyUI/run.sh --listen > output.log 2>&1 &')
            time.sleep(10)
            return await self.try_connect()
        


    async def stop_server(self):
        if await self.try_connect():
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connect to the server using key-based authentication
                client.connect(hostname=self.server_address, username=self.username, pkey=self.private_key)

                # not an ideal solution, but it works
                stdin, stdout, stderr = client.exec_command('nohup killall python3 > output.log 2>&1 &')

                if not await self.try_connect():
                    return "stopped"
                else:
                    return "not stopped"

        return "not running"