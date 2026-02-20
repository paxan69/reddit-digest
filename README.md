# 📰 Reddit Digest

A fully automated, free daily digest of your favourite subreddits delivered to your inbox every morning. No servers, no hosting, no Reddit account needed.

## How It Works

1. Fetches top posts and comments from your chosen subreddits via Reddit's RSS feed
2. Summarizes everything using Groq's free LLM API
3. Sends a formatted HTML email to your inbox
4. Runs automatically every day via GitHub Actions

## Project Structure

```
reddit-digest/
├── .github/
│   └── workflows/
│       └── digest.yml        # Automation schedule
├── config/
│   ├── config.yml            # Posts limit, score filter, email settings
│   ├── subreddits.txt        # One subreddit per line
│   └── prompt.txt            # LLM prompt — edit to change digest style
├── digest.py                 # Main script (no need to edit)
└── requirements.txt          # Python dependencies
```

## Setup

### 1. Get a Groq API Key (free)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up and go to **API Keys** → **Create API Key**
3. Copy the key

### 2. Get a Gmail App Password
1. Enable 2-Step Verification at [myaccount.google.com/security](https://myaccount.google.com/security)
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create a password named `reddit-digest` and copy the 16-character key

### 3. Add GitHub Secrets
In your repo go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |
| `EMAIL_ADDRESS` | Your Gmail address |
| `EMAIL_APP_PASSWORD` | Your 16-character app password |

### 4. Configure Your Digest

**`config/subreddits.txt`** — add one subreddit per line:
```
MachineLearning
entrepreneur
investing
```

**`config/config.yml`** — tune the digest behavior:
```yaml
posts_per_subreddit: 10      # How many posts to fetch per subreddit
min_score: 10                # Filter out posts below this score
max_tokens: 2000             # Length of the summary
email_to: you@gmail.com      # Who receives the digest
```

**`config/prompt.txt`** — edit this to change the structure, tone, or focus of the digest. No coding needed.

### 5. Test It
Go to **Actions** tab → **Daily Reddit Digest** → **Run workflow**. Check your inbox within a minute.

## Schedule

The digest runs every day at 8am UTC by default. To change the time edit `.github/workflows/digest.yml`:

```yaml
- cron: '0 8 * * *'
```

Common times:

| Timezone | Cron |
|---|---|
| UTC | `0 8 * * *` |
| London | `0 7 * * *` |
| Amsterdam/Paris | `0 7 * * *` |
| New York (EST) | `0 13 * * *` |
| Los Angeles (PST) | `0 16 * * *` |

## Email Setup (Gmail Filter)

If you send the digest to `yourname+reddit@gmail.com` you can filter it automatically:

1. In Gmail open **Settings** → **Filters** → **Create new filter**
2. In the **To** field enter `yourname+reddit@gmail.com`
3. Check **Skip Inbox** and **Apply label** → create a label called `Reddit Digest`
4. Optionally check **Mark as read**

Your digest will land in its own label, never cluttering your inbox.

## Customization

**Change subreddits** — edit `config/subreddits.txt`, one per line, no `r/` prefix needed.

**Change digest style** — edit `config/prompt.txt`. You can ask for bullet points, a different language, a focus on specific topics, or a completely different structure.

**Change delivery time** — edit the cron expression in `.github/workflows/digest.yml`.

**Change score filter** — raise `min_score` in `config/config.yml` to only see highly upvoted posts.

## Dependencies

- [feedparser](https://pypi.org/project/feedparser/) — parses Reddit RSS feeds
- [groq](https://pypi.org/project/groq/) — free LLM API for summarization
- [pyyaml](https://pypi.org/project/PyYAML/) — reads config file
- [requests](https://pypi.org/project/requests/) — fetches post comments

## Cost

Completely free:
- Reddit RSS feed — no account or API key needed
- Groq API — free tier is more than enough for one daily run
- GitHub Actions — free for this kind of lightweight scheduled job
- Gmail — free
