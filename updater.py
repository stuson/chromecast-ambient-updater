import os
import requests
import json
import mimetypes
from googleapiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from reddit_scraper import RedditScraper
from text_writer import add_text

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


def download_images():
    reddit_scraper = RedditScraper("C:/Users/Sam/Downloads/reddit_credentials.json")
    with open("subreddits.json") as subreddits_file:
        images = reddit_scraper.get_top_image_submissions(
            json.load(subreddits_file), limit=80
        )
    img_files = []

    for image in images:

        with requests.get(image["media_url"], stream=True) as res:
            try:
                if int(res.headers["Content-Length"]) > 52428800:  # Max 50MB
                    continue
            except KeyError:
                continue

            filename = image["id"]
            ext = mimetypes.guess_extension(res.headers["content-type"])

            try:
                filepath = os.path.join("downloaded_images", filename + ext)
            except TypeError:
                continue

            with open(filepath, "wb") as img_file:
                img_file.write(res.content)

        img_files.append(
            {
                "path": filepath,
                "filename": filename,
                "title": image["title"],
                "source": image["submission"].subreddit_name_prefixed,
            }
        )

    return img_files


def add_image_text(img_files):
    for img in img_files:
        add_text(img["path"], img["title"], "Source: " + img["source"])


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


def upload_photos(creds, img_files):
    # Caution: Deletes each photo as it is uploaded
    for img in img_files:
        url = "https://photoslibrary.googleapis.com/v1/uploads"
        authorization = "Bearer " + creds.token

        headers = {
            "Authorization": authorization,
            "Content-type": "application/octet-stream",
            "X-Goog-Upload-File-Name": img["title"].encode("utf-8"),
            "X-Goog-Upload-Protocol": "raw",
        }

        with open(img["path"], "rb") as img_file:
            res = requests.post(url, headers=headers, data=img_file)
        assert res.status_code == 200
        img["upload_token"] = res.text
        os.remove(img["path"])

    return img_files


def add_photos_to_album(service, album_id, img_files):
    i = 0
    while i < len(img_files):
        service.mediaItems().batchCreate(
            body={
                "albumId": album_id,
                "newMediaItems": [
                    {
                        "simpleMediaItem": {"uploadToken": img["upload_token"]},
                        "description": f"From {img['source']}",
                    }
                    for img in img_files[i : i + 50]
                ],
            }
        ).execute()
        i += 50


def main():
    creds = auth()
    service = build_service(creds)
    img_files = download_images()
    add_image_text(img_files)
    clear_photos(service, ALBUM_ID)
    img_files = upload_photos(creds, img_files)
    add_photos_to_album(service, ALBUM_ID, img_files)


if __name__ == "__main__":
    main()
