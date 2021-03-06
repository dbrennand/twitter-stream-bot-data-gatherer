"""
MIT License

Copyright (c) 2022 Daniel Brennand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import json
import sqlite3
import botometer
import tweepy
import logging
import os

# https://github.com/tweepy/tweepy/issues/908
from urllib3.exceptions import ProtocolError

# https://github.com/tweepy/tweepy/issues/237
# https://stackoverflow.com/questions/28717249/error-while-fetching-tweets-with-tweepy
from http.client import IncompleteRead


class CustomStreamListener(tweepy.StreamListener):
    """Subclass to handle the Twitter stream and sending accounts to Botometer for analysis.

    https://docs.tweepy.org/en/v3.10.0/streaming_how_to.html#streaming-with-tweepy
    """

    def __init__(
        self, bom: botometer.Botometer, con: sqlite3.Connection, cur: sqlite3.Cursor
    ):
        self.bom = bom
        self.con = con
        self.cur = cur
        super().__init__()

    def on_error(self, status_code: int):
        """Called when a non-200 status code is returned.

        Args:
            status_code (int): The HTTP status code returned by the Twitter stream.

        Returns:
            bool: `False` to disconnect from the Twitter stream.
                `True` to reconnect to the Twitter stream.
        """
        logging.error(f"Error code: {status_code} received from the Twitter stream.")
        if status_code == 420:
            logging.error(f"We're being rate limited! Disconnecting.")
            # We're being rate limited by the Twitter API so disconnect
            return False
        # Reconnect to the Twitter stream
        return True

    def on_status(self, status: tweepy.Status):
        """Called when a new status (Tweet) is received from the Twitter stream.
        Query the user of the Tweet to Botometer and store results.

        Args:
            status (tweepy.Status): The tweepy.Status model representation of a Tweet.
        """
        logging.info(
            f"Tweet received. Sending Twitter user: {status.user.screen_name} to Botometer for analysis."
        )
        # Query the Botometer API for the Twitter user's bot-like scores
        try:
            result = self.bom.check_account(status.user.id)
            logging.info("Storing results in database.")
            # Store the Twitter user's screen name, JSON response of the Tweet and Botometer API results
            self.cur.execute(
                "INSERT INTO data values (?, ?, ?)",
                [status.user.screen_name, json.dumps(status._json), json.dumps(result)],
            )
            self.con.commit()
        except botometer.NoTimelineError:
            logging.error(
                f"Twitter user: {status.user.screen_name} has no timeline. Continuing..."
            )
        except tweepy.TweepError as err:
            logging.error(
                f"Failed to query the Botometer API for Twitter user: {status.user.screen_name}\n{err}\nYour API quota may be exhausted if you see this message multiple times."
            )


if __name__ == "__main__":
    try:
        VERSION = "0.1.1"
        parser = argparse.ArgumentParser(
            description="An application to watch the Twitter stream and send accounts to the Botometer API for analysis. The results are stored in a SQLite database."
        )
        parser.add_argument("rapidapi_key", type=str, help="Botometer Rapid API key.")
        parser.add_argument(
            "twitter_app_auth", type=json.loads, help="Twitter application credentials."
        )
        parser.add_argument(
            "-t",
            "--track",
            action="append",
            help="A hashtag to track. Can be specified more than once.",
        )
        parser.add_argument(
            "-f",
            "--database_name",
            type=str,
            default="twitter-stream-bot-data-gatherer",
            help="Name of the database file. Defaults to: twitter-stream-bot-data-gatherer.",
        )
        parser.add_argument(
            "-d", "--debug", action="store_true", help="Enable debug messages."
        )
        args = parser.parse_args()
        # Set log level for application
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        logging.info(f"Starting twitter-stream-bot-data-gatherer version: {VERSION}")
        # Check db directory exists, if not, create it in current working directory
        db_dir = f"{os.getcwd()}/db"
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        # Initialise DB and table
        con = sqlite3.connect(f"db/{args.database_name}.db")
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS data (screen_name TEXT, status_json json, botometer_json json)"
        )
        con.commit()
        # Initialise Botometer
        bom = botometer.Botometer(
            wait_on_ratelimit=True,
            rapidapi_key=args.rapidapi_key,
            **args.twitter_app_auth,
        )
        # Initialise Tweepy OAuth handler
        auth = tweepy.OAuthHandler(
            consumer_key=args.twitter_app_auth["consumer_key"],
            consumer_secret=args.twitter_app_auth["consumer_secret"],
        )
        auth.set_access_token(
            key=args.twitter_app_auth["access_token"],
            secret=args.twitter_app_auth["access_token_secret"],
        )
        # Initialise Tweepy API
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        # Initialise custom stream listener
        stream_listener = CustomStreamListener(bom, con, cur)
        # Initialise Tweepy stream using custom stream listener
        stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
        # Begin tracking the Twitter stream
        logging.info(f"Tracking Twitter stream hashtag(s): {args.track}")
        while True:
            try:
                stream.filter(track=args.track, stall_warnings=True)
            except (IncompleteRead, ProtocolError) as err:
                # Most likely our client is falling behind
                # Reconnect to the Twitter stream and continue tracking
                logging.error(
                    f"An error occurred whilst tracking the Twitter stream:\n{err}\nReconnecting and continuing..."
                )
                continue
    except KeyboardInterrupt:
        con.close()
