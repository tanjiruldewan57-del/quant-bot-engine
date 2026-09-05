"""
================================================================================
💾 QUANT ENGINE STATE PERSISTENCE DAEMON (UPSTASH REDIS / CLOUD SYNC)
================================================================================
File: state_persistence.py
Purpose:
- Solves the Render Free Tier ephemeral disk data loss problem.
- Automatically restores bot state (USDT balance, ETH position, buy price) on boot.
- Continuously syncs modifications from local 'bot_state.json' to Upstash Redis.
- Supports both zero-dependency Upstash REST API (urllib.request) and redis-py.
================================================================================
"""

import os
import sys
import json
import time
import logging
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [STATE-SYNC] %(message)s"
)

STATE_FILE = "bot_state.json"
REDIS_KEY = "bot_state"

# Configuration from Environment Variables
UPSTASH_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "").rstrip("/")
UPSTASH_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
REDIS_URL = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL", "")

DEFAULT_STATE = {
    "eth_balance": 0.0,
    "usdt_balance": 100000.0,
    "buy_price": 0.0
}


def _fetch_from_upstash_rest() -> Optional[str]:
    """Retrieves state string from Upstash Redis via REST API (Zero Dependencies)."""
    if not UPSTASH_REST_URL or not UPSTASH_REST_TOKEN:
        return None
    try:
        url = f"{UPSTASH_REST_URL}/get/{REDIS_KEY}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {UPSTASH_REST_TOKEN}",
                "User-Agent": "QuantStatePersistence/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result")
    except Exception as e:
        logging.warning(f"⚠️ Failed to fetch state via Upstash REST: {e}")
        return None


def _push_to_upstash_rest(state_str: str) -> bool:
    """Pushes state string to Upstash Redis via REST API (Zero Dependencies)."""
    if not UPSTASH_REST_URL or not UPSTASH_REST_TOKEN:
        return False
    try:
        url = UPSTASH_REST_URL
        payload = json.dumps(["SET", REDIS_KEY, state_str]).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {UPSTASH_REST_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "QuantStatePersistence/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logging.warning(f"⚠️ Failed to push state via Upstash REST: {e}")
        return False


def _fetch_from_redis_client() -> Optional[str]:
    """Retrieves state string using standard redis-py library if installed and configured."""
    if not REDIS_URL:
        return None
    try:
        import redis
        client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
        return client.get(REDIS_KEY)
    except ImportError:
        return None
    except Exception as e:
        logging.warning(f"⚠️ Failed to fetch state via Redis client: {e}")
        return None


def _push_to_redis_client(state_str: str) -> bool:
    """Pushes state string using standard redis-py library if installed and configured."""
    if not REDIS_URL:
        return False
    try:
        import redis
        client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
        client.set(REDIS_KEY, state_str)
        return True
    except ImportError:
        return False
    except Exception as e:
        logging.warning(f"⚠️ Failed to push state via Redis client: {e}")
        return False


def is_cloud_redis_configured() -> bool:
    """Returns True if any cloud redis mechanism is provided."""
    return bool((UPSTASH_REST_URL and UPSTASH_REST_TOKEN) or REDIS_URL)


def validate_state(state: Dict[str, Any]) -> bool:
    """Enforces institutional sanity checks on portfolio state."""
    try:
        eth = float(state.get("eth_balance", 0.0))
        usdt = float(state.get("usdt_balance", 0.0))
        buy_price = float(state.get("buy_price", 0.0))

        if eth < 0.0 or usdt < 50000.0 or usdt > 10000000.0 or buy_price < 0.0:
            return False
        return True
    except (ValueError, TypeError):
        return False


def restore_state() -> Dict[str, Any]:
    """
    Called on boot before Rust engine starts.
    Pulls the latest verified state from cloud Redis and restores local bot_state.json.
    """
    logging.info("🔍 [RESTORE CHECK] Checking for remote state in cloud persistence layer...")
    state_str = None

    if UPSTASH_REST_URL and UPSTASH_REST_TOKEN:
        state_str = _fetch_from_upstash_rest()
    elif REDIS_URL:
        state_str = _fetch_from_redis_client()

    restored_state = None
    if state_str:
        try:
            parsed = json.loads(state_str)
            if validate_state(parsed):
                restored_state = parsed
                logging.info(
                    f"✅ [CLOUD RESTORE SUCCESS] Pulled state from Upstash Redis! "
                    f"USDT: ${restored_state['usdt_balance']:.2f} | "
                    f"ETH: {restored_state['eth_balance']:.4f} | "
                    f"Buy Price: ${restored_state['buy_price']:.2f}"
                )
            else:
                logging.warning("⚠️ Cloud state failed sanity check. Ignoring corrupt remote state.")
        except Exception as e:
            logging.warning(f"⚠️ Could not parse remote state JSON: {e}")

    # Fallback to local file if remote was not found or invalid
    if not restored_state and os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                parsed = json.load(f)
                if validate_state(parsed):
                    restored_state = parsed
                    logging.info(f"📂 [LOCAL RESTORE] Using existing local {STATE_FILE}.")
        except Exception as e:
            logging.warning(f"⚠️ Could not read local {STATE_FILE}: {e}")

    # Default if nothing exists
    if not restored_state:
        restored_state = DEFAULT_STATE.copy()
        logging.info(f"🌱 [INITIALIZATION] Initializing safe default state (USDT: ${DEFAULT_STATE['usdt_balance']:.2f})")

    # Write out local state file
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(restored_state, f, indent=2)
        logging.info(f"💾 [SYNC WRITTEN] Local {STATE_FILE} ready for Rust quant engine.")
    except Exception as e:
        logging.error(f"❌ Failed to write {STATE_FILE}: {e}")

    return restored_state


def persist_current_file() -> bool:
    """Reads local bot_state.json and mirrors it to cloud Redis."""
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read()
            parsed = json.loads(content)

        if not validate_state(parsed):
            logging.warning("⚠️ Local state invalid; skipping cloud push.")
            return False

        pushed = False
        if UPSTASH_REST_URL and UPSTASH_REST_TOKEN:
            pushed = _push_to_upstash_rest(content)
        elif REDIS_URL:
            pushed = _push_to_redis_client(content)

        if pushed:
            logging.info(f"☁️ [CLOUD BACKUP SYNCED] State mirrored to Upstash Redis (USDT: ${parsed['usdt_balance']:.2f}, ETH: {parsed['eth_balance']:.4f})")
        return pushed
    except Exception as e:
        logging.error(f"Error persisting state file: {e}")
        return False


def run_watcher_daemon():
    """
    Background worker that monitors bot_state.json for modifications
    and pushes new snapshots to Upstash Redis immediately.
    """
    logging.info("====================================================")
    logging.info("💾 STATE PERSISTENCE WATCHER DAEMON ACTIVE")
    if is_cloud_redis_configured():
        logging.info("🔒 Cloud Redis backend: CONFIGURED (Upstash/Redis sync enabled)")
    else:
        logging.warning("⚠️ Cloud Redis backend: NOT SET. Running in local-only disk mode.")
        logging.warning("💡 Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN in Render to survive container restarts.")
    logging.info("====================================================")

    last_mtime = 0.0
    last_heartbeat = time.time()

    while True:
        try:
            if os.path.exists(STATE_FILE):
                mtime = os.path.getmtime(STATE_FILE)
                if mtime > last_mtime:
                    last_mtime = mtime
                    persist_current_file()

            # Periodic heartbeat every 30 minutes
            if (time.time() - last_heartbeat) > 1800:
                last_heartbeat = time.time()
                logging.info("💓 [STATE-SYNC HEARTBEAT] Daemon active and monitoring bot_state.json.")

        except Exception as e:
            logging.error(f"Watcher exception: {e}")

        time.sleep(3)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "restore"
    if mode == "restore":
        restore_state()
    elif mode == "daemon":
        run_watcher_daemon()
    elif mode == "test":
        print("--- Self-Test Diagnostic ---")
        print(f"Cloud Configured: {is_cloud_redis_configured()}")
        print(f"REST URL: {'SET' if UPSTASH_REST_URL else 'UNSET'}")
        print(f"REST Token: {'SET' if UPSTASH_REST_TOKEN else 'UNSET'}")
        print(f"REDIS_URL: {'SET' if REDIS_URL else 'UNSET'}")
        st = restore_state()
        print(f"Active State: {st}")
    else:
        print(f"Unknown mode: {mode}. Use 'restore', 'daemon', or 'test'.")
