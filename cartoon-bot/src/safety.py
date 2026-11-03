import re
import config as C

_EN = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted(set(C.BLOCK_EN))) + r")\b", re.I)

def is_blocked(text):
    t = text or ""
    return bool(_EN.search(t)) or any(w in t for w in C.BLOCK_HI)

def filter_trends(items):
    return [i for i in items if not is_blocked(i)]

def story_text(st):
    parts = [st.get("topic", ""), st.get("title", ""), st.get("caption", ""), st.get("hook", "")]
    for s in st.get("scenes", []):
        parts += [s.get("narration", ""), s.get("image_prompt", "")]
    return " ".join(parts)

def local_check(st):
    m = _EN.search(story_text(st))
    if m:
        return False, f"blocked word '{m.group(0)}'"
    for w in C.BLOCK_HI:
        if w in story_text(st):
            return False, f"blocked word '{w}'"
    return True, ""
