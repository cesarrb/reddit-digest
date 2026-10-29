# reddit-digest

A small personal script that takes a daily, read-only snapshot of a few public subreddits so I can read private summaries of them.

## What it does

- Authenticates with Reddit's official Data API using application-only OAuth (`client_credentials`).
- Once a day, for each subreddit in `subreddits.json`, it reads:
  - the top posts of the month and the hot posts (up to 100 each);
  - the top comments of the 10 most discussed posts.
- Saves one JSON file per subreddit per day on my own computer.

That is roughly 2 + 10 = 12 requests per subreddit per day, one per second.

## What it does not do

- It never posts, comments, votes, messages or moderates.
- Content is not redistributed, published, sold or used to train any model.
- The private summaries are written on my own machine with help from an AI assistant (Claude) and are for my personal reading only.

## Use

Python 3.9+, standard library only.

```
# ~/.config/reddit-digest.env
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USERNAME=...
```

```
python3 fetch.py --out ~/reddit-digest-data
```

Credentials and downloaded data are excluded from this repository (`.gitignore`).

## License

MIT
