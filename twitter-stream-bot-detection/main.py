import argparse
import json
import sqlite3
import botometer
import tweepy
import logging

class CustomStreamListener(tweepy.StreamListener):
    """Subclass to handle Twitter stream and sending accounts to Botometer for analysis.
    """

    def __init__(self, bom, con, cur):
        self.bom = bom
        self.con = con
        self.cur = cur
        super().__init__(self)

    def on_error(self, status_code):
        print(status_code)
        return False

    def on_status(self, status):
        print(f"Tweet received: {status._json}")
        print(f"Sending Twitter user: {status.user.screen_name} to Botometer for analysis.")
        result = self.bom.check_account(status.user.id)
        print("Storing results in database.")
        self.cur.execute("INSERT INTO data values (?, ?, ?)", [status.user.screen_name, json.dumps(status._json), json.dumps(result)])
        self.con.commit()

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Watch the Twitter stream of a hashtag and send accounts to Botometer for analysis.")
        parser.add_argument("rapidapi_key", type=str, help="Botometer Rapid API key.")
        parser.add_argument("twitter_app_auth", type=json.loads, help="Twitter application credentials.")
        parser.add_argument("-t", "--track", action="append", help="A list of hashtags to track.")
        parser.add_argument("-f", "--database_name", type=str, default="twitter-stream-bot-detection", help="Name of the database file. Defaults to: twitter-stream-bot-detection.")
        parser.add_argument("-d", "--debug", action='store_true', help="Print debug messages.")
        args = parser.parse_args()
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
        # Initialise DB and table
        con = sqlite3.connect(f"{args.database_name}T{'-'.join(args.track)}.db")
        cur = con.cursor()
        cur.execute("CREATE TABLE data (screen_name TEXT, status_json json, botometer_json json)")
        con.commit()
        # Initialise Botometer
        bom = botometer.Botometer(wait_on_ratelimit=True, rapidapi_key=args.rapidapi_key, **args.twitter_app_auth)
        # Initialise Tweepy authentication handler
        auth = tweepy.AppAuthHandler(consumer_key=args.twitter_app_auth["consumer_key"], consumer_secret=args.twitter_app_auth["consumer_secret"])
        # Initialise Tweepy API
        api = tweepy.API(auth)
        # Create custom stream listener
        stream_listener = CustomStreamListener(bom, con, cur)
        # Initialise Tweepy stream using custom stream listener
        stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
        # Begin tracking
        print(f"Tracking Twitter stream hashtag(s): {args.track}")
        stream.filter(track=args.track)
    except KeyboardInterrupt:
        con.close()
