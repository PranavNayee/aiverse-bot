"""Poster job: publishes the queued reel at its slot time (see publisher.py)."""
import os, sys
import publisher
from util import log

if __name__ == "__main__":
    force = os.environ.get("FORCE_POST", "false").lower() == "true"
    wait = os.environ.get("WAIT_FOR_SLOT", "true").lower() == "true"
    try:
        log("Result:", publisher.run(force=force, wait=wait))
    except Exception:
        sys.exit(1)
