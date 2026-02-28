from app import create_app

import time
from flask import request

app = create_app()

@app.get("/health")
def health():
    return "ok", 200

@app.before_request
def _start_timer():
    request._start_time = time.time()

@app.after_request
def _log_request(response):
    dur = time.time() - getattr(request, "_start_time", time.time())
    app.logger.info("%s %s -> %s in %.3fs", request.method, request.path, response.status_code, dur)
    return response

if __name__ == "__main__":
    app.run()