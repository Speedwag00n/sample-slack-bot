import os
import logging
import slack
import commands.command_handler as command_handler


@slack.RTMClient.run_on(event="message")
def message(**payload):
    data = payload["data"]
    keys = command_handler.CommandHandler().commands
    for key in keys:
        if str(data["text"]).lower().startswith("!" + str(key)):
            try:
                keys[key].execute(payload)
            except Exception as e:
                logger.exception(e)
                channel_id = data["channel"]
                web_client = payload["web_client"]
                web_client.chat_postMessage(channel=channel_id, text="Unexpected error happened")
            break


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    token = os.environ["SLACK_SAMPLE_BOT_TOKEN"]
    rtm_client = slack.RTMClient(token=token)
    rtm_client.start()