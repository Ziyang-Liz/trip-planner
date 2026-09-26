import os, httpx

def http_timeout(default: int = 6):
    return httpx.Timeout(float(os.getenv("HTTP_TIMEOUT", default)))

def http_client():
    # you can add retry/proxy here if needed
    return httpx.AsyncClient(follow_redirects=True)
