#!/usr/bin/env python3
"""
Keep-alive service for HFT Tumar infrastructure.
Periodically pings all service endpoints to keep them warm.

Environment variables:
- KEEPALIVE_URLS: comma-separated list of URLs to ping
- KEEPALIVE_INTERVAL_SECONDS: interval between ping cycles (default: 120)
- KEEPALIVE_TIMEOUT_SECONDS: timeout for each request (default: 10)
- KEEPALIVE_LOG_LEVEL: logging level (default: INFO)
"""

import os
import sys
import time
import logging
import urllib.request
import urllib.error
import ssl
from datetime import datetime
from typing import List, Tuple

# Configuration from environment
URLS = os.getenv("KEEPALIVE_URLS", "").split(",")
INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "120"))
TIMEOUT = int(os.getenv("KEEPALIVE_TIMEOUT_SECONDS", "10"))
LOG_LEVEL = os.getenv("KEEPALIVE_LOG_LEVEL", "INFO").upper()

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("keepalive")

# SSL context that doesn't verify certificates (for internal services)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def ping_url(url: str) -> Tuple[int, float, str]:
    """
    Ping a URL and return (status_code, response_time_ms, error_message).
    """
    url = url.strip()
    if not url:
        return 0, 0, "empty URL"
    
    start_time = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Tumar-Keepalive/1.0"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as response:
            status_code = response.getcode()
            response_time = (time.time() - start_time) * 1000  # ms
            return status_code, response_time, ""
    except urllib.error.HTTPError as e:
        response_time = (time.time() - start_time) * 1000
        return e.code, response_time, str(e.reason)
    except urllib.error.URLError as e:
        response_time = (time.time() - start_time) * 1000
        return 0, response_time, str(e.reason)
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return 0, response_time, str(e)


def ping_all_urls(urls: List[str]) -> dict:
    """Ping all URLs and return statistics."""
    results = {"success": 0, "failed": 0, "total": 0}
    
    for url in urls:
        url = url.strip()
        if not url:
            continue
        
        results["total"] += 1
        status, response_time, error = ping_url(url)
        
        if 200 <= status < 400:
            results["success"] += 1
            logger.info(f"✓ {url} - {status} ({response_time:.0f}ms)")
        else:
            results["failed"] += 1
            logger.warning(f"✗ {url} - {status} ({response_time:.0f}ms) - {error}")
    
    return results


def main():
    """Main loop."""
    logger.info("=" * 60)
    logger.info("Tumar Keep-alive Service Starting")
    logger.info(f"Interval: {INTERVAL}s, Timeout: {TIMEOUT}s")
    logger.info(f"URLs to ping: {len([u for u in URLS if u.strip()])}")
    logger.info("=" * 60)
    
    if not URLS or not any(u.strip() for u in URLS):
        logger.error("No URLs configured! Set KEEPALIVE_URLS environment variable.")
        sys.exit(1)
    
    for url in URLS:
        if url.strip():
            logger.info(f"  - {url.strip()}")
    
    cycle = 0
    while True:
        cycle += 1
        logger.info(f"--- Ping cycle #{cycle} started ---")
        
        results = ping_all_urls(URLS)
        
        logger.info(
            f"--- Cycle #{cycle} complete: "
            f"{results['success']}/{results['total']} OK, "
            f"{results['failed']} failed ---"
        )
        
        logger.debug(f"Sleeping for {INTERVAL} seconds...")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()

