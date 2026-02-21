from groq import Groq
import feedparser
import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
from datetime import date

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def load_config():
    with open("config/config.yml", "r") as f:
        return yaml.safe_load(f)

def load_subreddits():
    with open("config/subreddits.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def load_prompt():
    with open("config/prompt.txt", "r") as f:
        return f.read()


def fetch_posts(subreddits, limit, min_score):
    print("Fetching posts...")
    posts = []
    seen_titles = set()

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/top.rss?t=day&limit={limit}"
            feed = feedparser.parse(url)

            if not feed.entries:
                print(f"  r/{sub}: no posts found, skipping")
                continue

            count = 0
            for entry in feed.entries:
                title = entry.title.strip()

                if title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                score = extract_score(entry)
                if score is not None and score < min_score:
                    continue

                summary = entry.summary[:500] if hasattr(entry, "summary") else ""
                link = entry.link if hasattr(entry, "link") else ""

                # Fetch top comments via JSON API
                comments = fetch_comments(link)

                posts.append(
                    f"[r/{sub}] {title}\n"
                    f"URL: {link}\n"
                    f"Score: {score}\n"
                    f"Post: {summary}\n"
                    f"Top comments:\n{comments}"
                )
                count += 1

            print(f"  r/{sub}: {count} posts fetched")

        except Exception as e:
            print(f"  r/{sub}: failed to fetch — {e}")
            continue

    return "\n\n---\n\n".join(posts)

def fetch_comments(post_url):
    import requests
    import time
    try:
        # Use RSS for comments instead of JSON API — not blocked
        clean_url = "/".join(post_url.rstrip("/").split("/")[:7])
        rss_url = clean_url + ".rss?limit=5&sort=top"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; daily-digest-bot/1.0)"}
        time.sleep(1)
        feed = feedparser.parse(rss_url)
        comments = []
        for entry in feed.entries[1:6]:  # skip first entry which is the post itself
            body = entry.summary if hasattr(entry, "summary") else ""
            # Strip HTML tags
            body = re.sub(r"<[^>]+>", "", body).strip()[:300]
            if body and body not in ("[deleted]", "[removed]"):
                comments.append(f"  • {body}")
        return "\n".join(comments) if comments else "  No comments available"
    except Exception as e:
        return f"  Could not fetch comments: {e}"
        
        
def extract_score(entry):
    # Reddit RSS embeds the score in the summary HTML
    try:
        match = re.search(r"(\d+) point", entry.summary)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None

def summarize(posts, max_tokens):
    print("Summarizing with Groq...")
    try:
        prompt = load_prompt()
        full_prompt = f"{prompt}\n\nReddit posts:\n{posts}"
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Groq summarization failed: {e}")

def to_html(text):
    # Convert markdown-style output to clean HTML
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("- **") or line.startswith("- "):
            content = line[2:]
            content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
            # Make URLs clickable
            content = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', content)
            html_lines.append(f"<li>{content}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', line)
            html_lines.append(f"<p>{line}</p>")

    body = "\n".join(html_lines)
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto; padding: 20px; color: #222;">
        <h1 style="border-bottom: 2px solid #ff4500; padding-bottom: 10px;">
            📰 Daily Reddit Digest — {date.today().strftime("%B %d, %Y")}
        </h1>
        {body}
        <hr>
        <p style="color: #999; font-size: 12px;">Generated automatically from r/{", r/".join(load_subreddits())}</p>
    </body>
    </html>
    """

def send_email(summary, email_to):
    print("Sending email...")
    today = date.today().strftime("%B %d, %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📰 Daily Reddit Digest — {today}"
    msg["From"] = os.environ["EMAIL_ADDRESS"]
    msg["To"] = email_to

    # Plain text fallback
    msg.attach(MIMEText(summary, "plain"))
    # HTML version
    msg.attach(MIMEText(to_html(summary), "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_ADDRESS"], os.environ["EMAIL_APP_PASSWORD"])
        server.send_message(msg)
    print("✅ Email sent successfully!")

def send_error_email(error):
    print("Sending error notification...")
    msg = MIMEMultipart()
    msg["Subject"] = "⚠️ Reddit Digest Failed"
    msg["From"] = os.environ["EMAIL_ADDRESS"]
    msg["To"] = os.environ["EMAIL_ADDRESS"]
    msg.attach(MIMEText(f"Your daily Reddit digest failed with this error:\n\n{error}", "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.environ["EMAIL_ADDRESS"], os.environ["EMAIL_APP_PASSWORD"])
            server.send_message(msg)
    except Exception as e:
        print(f"Could not send error email: {e}")

if __name__ == "__main__":
    try:
        config = load_config()
        subreddits = load_subreddits()

        posts = fetch_posts(
            subreddits,
            limit=config["posts_per_subreddit"],
            min_score=config["min_score"]
        )

        if not posts:
            raise RuntimeError("No posts fetched from any subreddit.")

        summary = summarize(posts, max_tokens=config["max_tokens"])

        print("\n--- SUMMARY PREVIEW ---")
        print(summary)

        send_email(summary, email_to=config["email_to"])

    except Exception as e:
        print(f"❌ Error: {e}")
        send_error_email(str(e))
        exit(1)
