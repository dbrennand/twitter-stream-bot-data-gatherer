# twitter-stream-bot-data-gatherer

An application to watch the Twitter stream and send accounts to the [Botometer API](https://botometer.osome.iu.edu/) for analysis. The results are stored in a SQLite database.

## Prerequisites

Before using this application, credentials for the following are required:

  * [The Twitter API](https://developer.twitter.com/en/docs)

  * [The Botometer API](https://rapidapi.com/OSoMe/api/botometer-pro)

### Twitter API Credentials

The application connects to the Twitter stream API to query Twitter user's to Botometer for analysis.

To get access to the Twitter API, a developer account is needed. You can apply for one [here](https://developer.twitter.com/en/apply-for-access) and find more information about the application process [here](https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api).

Once you have a developer account, go to the [developer portal](https://developer.twitter.com/en/portal/dashboard) to create an application.

When creating the application, provide a unique *name* and follow the instructions. The application's API key and secret will be shown (aka. `consumer_key` and `consumer_secret`). Furthermore, you will need to generate an access token and access token secret to use the Twitter stream API. Go to your application, click **Keys and tokens** > **Access Token and Secret** > **Generate**. Store the credentials somewhere safe as they will be needed later.

### Botometer API Credentials

The application uses the [Botometer API](https://rapidapi.com/OSoMe/api/botometer-pro/details) to collect bot scores for Twitter users.

To get access to the Botometer API, a RapidAPI account is needed. You can create one [here](https://rapidapi.com/auth/sign-up).

Once you have a RapidAPI account, go to the Botometer API [pricing](https://rapidapi.com/OSoMe/api/botometer-pro/pricing) page and subscribe to the *Basic* or *Pro* plan.

> [!NOTE]
>
> The *Pro* plan requires a credit or debit card to be added to the RapidAPI account.

Once you have chosen a plan, go to the RapidAPI [developer dashboard](https://rapidapi.com/developer/apps). Then, go to security page for the `default-application`. The application key (API key) will be shown. Store it somewhere safe as it will be needed later.

Further details on accessing the Botometer API can be found [here](https://github.com/IUNetSci/botometer-python#rapidapi-and-twitter-access-details).

## Dependencies

Install the application's dependencies using one of the options below:

```bash
# Poetry
poetry install --no-dev
# Pip
pip install -r requirements.txt
# Or use Docker!
# Please refer to the heading below
```

## Usage

```
$ python twitter-stream-bot-data-gatherer/main.py -h

usage: main.py [-h] [-t TRACK] [-f DATABASE_NAME] [-d]
               rapidapi_key twitter_app_auth

An application to watch the Twitter stream and send accounts to the Botometer
API for analysis. The results are stored in a SQLite database.

positional arguments:
  rapidapi_key          Botometer Rapid API key.
  twitter_app_auth      Twitter application credentials.

optional arguments:
  -h, --help            show this help message and exit
  -t TRACK, --track TRACK
                        A hashtag to track. Can be specified more than once.
  -f DATABASE_NAME, --database_name DATABASE_NAME
                        Name of the database file. Defaults to: twitter-
                        stream-bot-data-gatherer.
  -d, --debug           Enable debug messages.
```

### Tracking a Single Hashtag

```bash
python twitter-stream-bot-data-gatherer/main.py <rapidapi_key> \
  '{"consumer_key": "", "consumer_secret": "", "access_token": "", "access_token_secret": ""}' \
  --track '#StandWithUkriane'
```

### Tracking Multiple Hashtags

```bash
python twitter-stream-bot-data-gatherer/main.py <rapidapi_key> \
  '{"consumer_key": "", "consumer_secret": "", "access_token": "", "access_token_secret": ""}' \
  -t '#StandWithUkriane' \
  -t '#RefugeesWelcome' \
  -t '#Ukrania'
```

### Modifying the SQLite Database Name

```bash
python twitter-stream-bot-data-gatherer/main.py <rapidapi_key> \
  '{"consumer_key": "", "consumer_secret": "", "access_token": "", "access_token_secret": ""}' \
  -t '#StandWithUkriane' \
  # The database will be named 'twitter-db.db'
  -f 'twitter-db'
```

### Docker 🐋

Build the container image:

```bash
docker build -t twitter-stream-bot-data-gatherer:v0.1.0 .
```

Run the application and persist the SQLite database:

```bash
docker run -it --name twitter-stream-bot-data-gatherer \
    -v absolute/path/to/store/db:/usr/src/app/db \
    twitter-stream-bot-data-gatherer:v0.1.0 <rapidapi_key> \
    '{"consumer_key": "", "consumer_secret": "", "access_token": "", "access_token_secret": ""}' \
    --track '#StandWithUkriane'
```

## Database Structure

The database will contain one table called `data`. Within the table will be three columns:

1. `screen_name`: The screen name of the Twitter account.

2. `status_json`: The full JSON response of the [Tweet Object (aka. Status)](https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/tweet) from the Twitter stream.

3. `botometer_json`: The full JSON response from the Botometer API.

## My Related Work

* [dbrennand/Final-Year-Project](https://github.com/dbrennand/Final-Year-Project) - An application that generates a report to identify potential bots that a Twitter user is following.

## Acknowledgments

This application would not be possible without the work of the [Observatory on Social Media at Indiana University](https://osome.iu.edu/) who created Botometer. Please see the [Botometer FAQ](https://botometer.osome.iu.edu/faq) page for further information on Botometer.

## Authors -- Contributors

* [**dbrennand**](https://github.com/dbrennand) - *Author*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.
