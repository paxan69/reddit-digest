from groq import Groq
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ==============================
# EDIT YOUR SUBREDDITS HERE
# ==============================
SUBREDDITS = ["MachineLearning", "entrepreneur", "investing"]

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def fetch_posts():
    print("Fetching posts...")
    posts = []
    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/top.rss?t=day&limit=10"
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title
            summary = entry.summary[:300] if hasattr(entry, "summary") else ""
            posts.append(f"[r/{sub}] {title}\n{summary}")
        print(f"  r/{sub}: {len(feed.entries)} posts fetched")
    return "\n\n---\n\n".join(posts)

def summarize(posts):
    print("Summarizing with Groq...")
    prompt = f"""You are a daily briefing assistant. Analyze these Reddit posts from today and produce a clean, useful digest.

Structure your response as:

## 🔥 Key Trends
(2-3 bullet points on what topics are dominating today)

## ✅ Actionable Insights
(3-5 specific things I can act on today based on what people are discussing)

## 📌 Must-Read Posts
(Top 3 posts worth my time, with a one-line summary of why each matters)

## 🗑️ What to Skip
(What's just noise or not worth time today)

Be direct, specific, and opinionated. Avoid vague advice.

Reddit posts:
{posts}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response.choices[0].message.content

def send_email(summary):
    print("Sending email...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📰 Your Daily Reddit Digest"
    msg["From"] = os.environ["EMAIL_ADDRESS"]
    msg["To"] = os.environ["EMAIL_ADDRESS"]
    msg.attach(MIMEText(summary, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_ADDRESS"], os.environ["EMAIL_APP_PASSWORD"])
        server.send_message(msg)
    print("✅ Email sent successfully!")

if __name__ == "__main__":
    posts = fetch_posts()
    if not posts:
        print("No posts found. Exiting.")
        exit(1)
    summary = summarize(posts)
    print("\n--- SUMMARY PREVIEW ---")
    print(summary)
    send_email(summary)
