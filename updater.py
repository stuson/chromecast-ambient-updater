import os
from googleapiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import requests

SCOPES = ("https://www.googleapis.com/auth/photoslibrary",)
ALBUM_ID = (
    "ACKRuAdbBPByGYlApSNkZCjSBdTooYH2upyamsUOdR4nYyOWZ0WPHcp8IiVpAOFJ7t16Mb8zJeJj"
)


def auth():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "C:/Users/Sam/Downloads/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def build_service(creds):
    return discovery.build(
        "photoslibrary", "v1", credentials=creds, static_discovery=False
    )


def clear_photos(service, album_id):
    ids = []
    page_token = None

    while True:
        res = (
            service.mediaItems()
            .search(body={"albumId": album_id, "pageToken": page_token})
            .execute()
        )

        try:
            ids.extend(item["id"] for item in res["mediaItems"])
        except KeyError:
            return

        try:
            page_token = res["nextPageToken"]
        except KeyError:
            break

    service.albums().batchRemoveMediaItems(
        albumId=album_id,
        body={"mediaItemIds": ids},
    ).execute()


def upload_photos(creds, dir):
    upload_tokens = []
    _, _, filepaths = next(os.walk(dir))

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        url = "https://photoslibrary.googleapis.com/v1/uploads"
        authorization = "Bearer " + creds.token

        headers = {
            "Authorization": authorization,
            "Content-type": "application/octet-stream",
            "X-Goog-Upload-File-Name": filename,
            "X-Goog-Upload-Protocol": "raw",
        }

        with open(os.path.join(dir, filepath), "rb") as image_file:
            res = requests.post(url, headers=headers, data=image_file)
        upload_tokens.append(res.text)

    return upload_tokens


def add_photos_to_album(service, album_id, upload_tokens):
    service.mediaItems().batchCreate(
        body={
            "albumId": album_id,
            "newMediaItems": [
                {
                    "simpleMediaItem": {"uploadToken": upload_token},
                    "description": "Chromecast Ambient Updater automatic upload",
                }
                for upload_token in upload_tokens
            ],
        }
    ).execute()


def main():
    creds = auth()
    service = build_service(creds)
    clear_photos(service, ALBUM_ID)
    upload_tokens = upload_photos(creds, "C:/Users/Sam/Pictures/test_uploads")
    add_photos_to_album(service, ALBUM_ID, upload_tokens)


if __name__ == "__main__":
    main()
