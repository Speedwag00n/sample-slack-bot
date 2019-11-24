import commands.command as command
import os
import os.path
import requests
from pyunpack import Archive
import json
from PIL import Image


class Greeting(command.Command):

    variants = ["hi", "hello"]

    def execute(self, payload):
        data = payload["data"]
        web_client = payload["web_client"]
        channel_id = data["channel"]
        user = data["user"]
        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Hi, <@{user}>!",
        )


class Compress(command.Command):

    STORAGE_PATH = "temp/"
    variants = ["comp", "compress"]

    def execute(self, payload):
        data = payload["data"]
        file_url = data["files"][0]["url_private_download"]
        file_path = self.STORAGE_PATH + data["files"][0]["id"]
        file_name = file_path + "_" + data["files"][0]["name"]
        web_client = payload["web_client"]
        channel_id = data["channel"]
        token = os.environ["SLACK_SAMPLE_BOT_TOKEN"]
        response = requests.get(file_url, headers={"Authorization": "Bearer " + token})
        if response.status_code == 200:
            os.mkdir(self.STORAGE_PATH + data["files"][0]["id"])
            open(file_name, "wb").write(response.content)
            Archive(file_name).extractall(file_path)

            with open(file_path + "/config.json") as config:
                config_data = json.load(config)

            width = int(config_data["size_x"])
            height = int(config_data["size_y"])

            if os.path.exists(file_path + "/image.png"):
                image = Image.open(file_path + "/image.png")
                resized_image = image.resize((width, height), Image.ANTIALIAS)
                resized_image.save(file_path + "/image.png")
                web_client.files_upload(
                    channels=channel_id,
                    file=file_path + "/image.png"
                )
            elif os.path.exists(file_path + "/image.jpg"):
                image = Image.open(file_path + "/image.jpg")
                resized_image = image.resize((width, height), Image.ANTIALIAS)
                resized_image.save(file_path + "/image.jpg")
                web_client.files_upload(
                    channels=channel_id,
                    file=file_path + "/image.jpg"
                )
            else:
                message = "Image in archive not found: it must contain image with name image.png or image.jpg"
        else:
            message = "Can't download file"
        web_client.chat_postMessage(
            channel=channel_id,
            text=message,
        )
