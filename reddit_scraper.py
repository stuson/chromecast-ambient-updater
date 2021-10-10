import requests
import praw
import json
import mimetypes


class RedditScraper:
    def __init__(self, creds_file):
        with open(creds_file, "r") as creds_file:
            creds = json.load(creds_file)

        self.reddit = praw.Reddit(**creds)

    def get_top_image_submissions(self, subreddits, time_filter="week", **kwargs):
        submissions = self.reddit.subreddit("+".join(subreddits)).top(
            time_filter, **kwargs
        )
        for submission in submissions:
            try:
                if submission.post_hint == "image":
                    yield {
                        "submission": submission,
                        "media_url": submission.url,
                        "title": submission.title,
                        "id": submission.id,
                    }
            except AttributeError:
                try:
                    if submission.is_gallery:
                        i = 0
                        for media_id in submission.media_metadata:
                            i += 1
                            yield {
                                "submission": submission,
                                "media_url": submission.media_metadata[media_id]["s"][
                                    "u"
                                ],
                                "title": submission.title + f" [Gallery Image {i}]",
                                "id": media_id,
                            }
                except AttributeError:
                    pass
