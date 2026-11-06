#!/usr/bin/env bash
# Installs ffmpeg + the Noto fonts WITHOUT depending on the Ubuntu apt mirror (it hangs on the new
# Ubuntu 26.04 runners). Downloads come from GitHub-hosted builds; apt is only the last resort.
# Downloads are kept in ~/.cache/media so actions/cache can reuse them.
set -u
CACHE="$HOME/.cache/media"; mkdir -p "$CACHE"
get() {  # get <out> <url>...   (first URL that works wins)
  local out="$1"; shift
  [ -s "$out" ] && return 0
  for u in "$@"; do
    curl -fsSL --retry 3 --retry-delay 3 --connect-timeout 15 --max-time 240 -o "$out.part" "$u" && mv "$out.part" "$out" && return 0
    echo "  download failed: $u"
  done
  rm -f "$out.part"; return 1
}

# ---- ffmpeg + ffprobe
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  if get "$CACHE/ffmpeg.tar.xz" \
       https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz \
       https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz; then
    rm -rf /tmp/ffx && mkdir -p /tmp/ffx && tar -xf "$CACHE/ffmpeg.tar.xz" -C /tmp/ffx
    sudo install -m 755 $(find /tmp/ffx -type f \( -name ffmpeg -o -name ffprobe \) ) /usr/local/bin/
  else
    echo "static ffmpeg unavailable - trying apt"
    sudo timeout 240 apt-get update -qq && sudo timeout 300 apt-get install -y -qq ffmpeg
  fi
fi
ffmpeg -hide_banner -version | head -1 || { echo "ffmpeg missing"; exit 1; }

# ---- fonts (non-fatal: the renderer falls back to DejaVu / built-in fonts)
NOTO=https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts
sudo mkdir -p /usr/share/fonts/truetype/noto
for f in NotoSans/hinted/ttf/NotoSans-Bold NotoSans/hinted/ttf/NotoSans-Regular \
         NotoSansMono/hinted/ttf/NotoSansMono-Bold NotoSansMono/hinted/ttf/NotoSansMono-Regular; do
  n=$(basename "$f").ttf
  get "$CACHE/$n" "$NOTO/$f.ttf" && sudo cp "$CACHE/$n" /usr/share/fonts/truetype/noto/ || echo "font $n skipped"
done
get "$CACHE/NotoColorEmoji.ttf" \
    https://github.com/googlefonts/noto-emoji/raw/v2.047/fonts/NotoColorEmoji.ttf \
    https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/fonts/NotoColorEmoji.ttf \
  && sudo cp "$CACHE/NotoColorEmoji.ttf" /usr/share/fonts/truetype/noto/ || echo "emoji font skipped"
command -v fc-cache >/dev/null && sudo fc-cache -f >/dev/null 2>&1
ls /usr/share/fonts/truetype/noto/
exit 0
