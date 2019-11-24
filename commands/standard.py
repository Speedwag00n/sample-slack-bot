import commands.command as command


class Greeting(command.Command):

    variants = ["hi", "hello"]

    def execute(self, payload):
        data = payload["data"]
        web_client = payload['web_client']
        channel_id = data['channel']
        user = data['user']
        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Hi, <@{user}>!",
        )