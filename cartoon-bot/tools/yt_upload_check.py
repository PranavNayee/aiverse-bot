"""Uploads the offline-test reel to the connected YouTube channel as PRIVATE and prints the channel + link."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import youtube

os.environ["YT_PRIVACY"] = "private"
tok = youtube._access_token()
ch = youtube._api("GET", "channels", tok, params={"part": "snippet", "mine": "true"})["items"][0]["snippet"]["title"]
print("Connected channel:", ch)
if ch.strip().lower() != os.environ.get("YT_EXPECTED_CHANNEL", "AIVerse").lower():
    sys.exit(f"Refusing to upload: connected channel is {ch!r}")
path = sys.argv[1] if len(sys.argv) > 1 else "test_work/reel.mp4"
title = sys.argv[2] if len(sys.argv) > 2 else "AIVerse bot test upload"
vid = youtube.upload(path, "Private preview from AIVerse Bot.", title, "test", ["#aiverse"])
print("Uploaded PRIVATE test Short:", f"https://youtube.com/shorts/{vid}")
