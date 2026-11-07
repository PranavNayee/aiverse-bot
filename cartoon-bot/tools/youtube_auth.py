"""One-time YouTube authorisation. Run on YOUR computer:

    python cartoon-bot/tools/youtube_auth.py client_secret_XXXX.json      (the file downloaded from Google Cloud)
    python cartoon-bot/tools/youtube_auth.py CLIENT_ID CLIENT_SECRET       (or paste the two values)

Before that, in https://console.cloud.google.com : create a project -> enable "YouTube Data API v3" ->
OAuth consent screen (External, add yourself as a test user, then "Publish app") -> Credentials ->
Create OAuth client ID -> type "Desktop app". Use that client id/secret here.
A browser opens; pick the YouTube channel to post to. The refresh token is then saved to the GitHub
secrets (via the gh CLI) - it is never printed."""
import http.server, json, os, subprocess, sys, threading, urllib.parse, urllib.request, webbrowser

PORT = 8765
SCOPE = ("https://www.googleapis.com/auth/youtube.upload "      # upload Shorts
         "https://www.googleapis.com/auth/youtube.force-ssl")    # playlists + replying to comments


def main():
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):       # the client_secret_*.json file from Google Cloud
        d = json.load(open(sys.argv[1]))
        d = d.get("installed") or d.get("web") or d
        cid, secret = d["client_id"], d["client_secret"]
    elif len(sys.argv) == 3:
        cid, secret = sys.argv[1], sys.argv[2]
    else:
        sys.exit(__doc__)
    redirect = f"http://127.0.0.1:{PORT}"
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Done - you can close this tab and go back to the terminal.")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent"})
    print("Opening browser for Google sign-in...\nIf it does not open, visit:\n" + url)
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        threading.Event().wait(0.5)
    if "error" in got:
        sys.exit("Authorisation refused: " + got["error"])
    body = urllib.parse.urlencode({"code": got["code"], "client_id": cid, "client_secret": secret,
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    tok = json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", body).read())
    if "refresh_token" not in tok:
        sys.exit(f"No refresh token returned: {tok}")
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
                                 headers={"Authorization": "Bearer " + tok["access_token"]})
    chans = json.loads(urllib.request.urlopen(req).read()).get("items", [])
    name = chans[0]["snippet"]["title"] if chans else "?"
    print(f"Connected YouTube channel: {name}")
    expected = os.environ.get("YT_EXPECTED_CHANNEL", "AIVerse")
    if name.strip().lower() != expected.strip().lower():      # works without a keyboard prompt (e.g. `! cmd`)
        sys.exit(f"❌ That is '{name}', not '{expected}'. Nothing saved - run again and pick the {expected} channel "
                 f"(or set YT_EXPECTED_CHANNEL).")
    for name, val in (("YT_CLIENT_ID", cid), ("YT_CLIENT_SECRET", secret), ("YT_REFRESH_TOKEN", tok["refresh_token"])):
        subprocess.run(["gh", "secret", "set", name], input=val.encode(), check=True)
    print("✅ Saved YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN to GitHub secrets. Shorts cross-posting is on.")


if __name__ == "__main__":
    main()
