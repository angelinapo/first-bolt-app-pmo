import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from googleapiclient import discovery
from google.oauth2 import service_account
from datetime import datetime

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


# logging.basicConfig(level=logging.DEBUG)

@app.event("message")
def handle_message_events(ack):
    ack()

@app.event("reaction_removed")
def handle_reaction_removed_events(ack):
    ack()


@app.event("reaction_added")
def handle_reaction_added_events(ack, body, say, client):
    # Acknowledge action request
    ack()
    # logging.warning(body)

    if body['event']['reaction'] == 'white_check_mark':
        messages = client.conversations_replies(
            channel=body["event"]["item"]["channel"],
            ts=body["event"]["item"]["ts"]
        )
        origin = messages["messages"][0]
        user_id = origin["user"]
        client.chat_postMessage(
            channel=body["event"]["item"]["channel"],
            text=f"<@{user_id}> мы решили твою задачу, оцени результат реакцией от :one: до :five:",
            thread_ts=body["event"]["item"]["ts"]
        )
    elif body['event']['reaction'] in ['one', 'two', 'three', 'four', 'five']:
        t_messages = client.conversations_replies(
            channel=body["event"]["item"]["channel"],
            ts=body["event"]["item"]["ts"]
        )
        messages = client.conversations_replies(
            channel=body["event"]["item"]["channel"],
            ts=t_messages["messages"][0]["thread_ts"]
        )
        origin = messages["messages"][0]
        origin_link = client.chat_getPermalink(
            channel=body["event"]["item"]["channel"],
            message_ts=origin["ts"]
        )
        customer = client.users_info(user=origin["user"])
        origin_check = list(filter(lambda f: (f["name"] == "white_check_mark"), origin["reactions"]))
        # logging.warning(origin_check)

        executor = client.users_info(user=origin_check[0]["users"][0])
        if body['event']['user'] == origin["user"]:

            now = datetime.now()
            row = [
                now.strftime("%m/%d/%Y"),
                origin_link["permalink"],
                customer["user"]["real_name"],
                executor["user"]["real_name"],
                body['event']['reaction']
            ]
            app_to_file(row)


def app_to_file(body):
    SCOPES = [
        'https://www.googleapis.com/auth/sqlservice.admin',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    SERVICE_ACCOUNT_FILE = 'token.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = discovery.build('sheets', 'v4', credentials=credentials)

    spreadsheet_id = '1XjX4OJbU0sK2f03-BmUkUWoV38uEtVwL8TbmLi78hLU'
    range_ = 'A1:E1'
    value_input_option = 'RAW'
    insert_data_option = 'INSERT_ROWS'

    value_range_body = {
        "values": [
            body
        ],
        "majorDimension": "ROWS"
    }

    request = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption=value_input_option,
        insertDataOption=insert_data_option,
        body=value_range_body
    )
    request.execute()


# Start your app
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
