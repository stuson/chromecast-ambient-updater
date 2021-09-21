import requests
import praw
import json
import mimetypes


class RedditScraper:
    def __init__(self, creds_file):
        with open(creds_file, "r") as creds_file:
            creds = json.load(creds_file)

        self.reddit = praw.Reddit(**creds)

    def get_top_image_submissions(self, subreddits, time_filter="week"):
        submissions = self.reddit.subreddit("+".join(subreddits)).top(time_filter)
        for submission in submissions:
            try:
                if submission.post_hint == "image":
                    yield {"submission": submission, "media_url": submission.url}
            except AttributeError:
                try:
                    if submission.is_gallery:
                        for media_id in submission.media_metadata:
                            yield {
                                "submission": submission,
                                "media_url": submission[media_id]["s"]["u"],
                            }
                except AttributeError:
                    pass
