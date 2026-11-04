"""Finds the speaking character's mouth in a picture (Gemini vision) so we can animate it."""
import base64, io, requests
from PIL import Image
import config as C
from story import _clean_json
from util import log

PROMPT = """This is a 3D cartoon image. Find the mouth of this character: {who}.
Return ONLY JSON: {{"found": true or false, "x": 0.0-1.0, "y": 0.0-1.0, "w": 0.0-1.0}}
x and y = centre of the mouth as a fraction of image width / height measured from the TOP-LEFT corner.
w = width of the mouth as a fraction of image width. If the character has no clearly visible mouth, found=false."""

def detect(img_path, speaker):
    """Returns {'x','y','w'} (fractions) or None. Never raises."""
    if speaker not in C.CHARACTERS:
        return None
    try:
        im = Image.open(img_path).convert("RGB")
        im.thumbnail((768, 768))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
        body = {"contents": [{"parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}},
                    {"text": PROMPT.format(who=C.CHARACTERS[speaker]["look"])}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
        for m in C.GEMINI_MODELS:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                              headers={"x-goog-api-key": C.GEMINI_API_KEY(), "Content-Type": "application/json"},
                              json=body, timeout=90)
            if r.status_code == 200:
                j = _clean_json(r.json()["candidates"][0]["content"]["parts"][0]["text"])
                if j.get("found") and 0.05 <= j["x"] <= 0.95 and 0.05 <= j["y"] <= 0.95 and 0.04 <= j["w"] <= 0.5:
                    return {"x": float(j["x"]), "y": float(j["y"]), "w": float(j["w"])}
                return None
        return None
    except Exception as e:
        log("  mouth detection skipped:", str(e)[:150])
        return None
