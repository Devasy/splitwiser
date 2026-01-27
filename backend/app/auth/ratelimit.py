import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# In-memory storage for rate limiting
# In a production environment, you might want to use Redis or another shared storage.
rate_limit_data = defaultdict(lambda: {"count": 0, "timestamp": 0})
RATE_LIMIT_DURATION = 60  # seconds
RATE_LIMIT_REQUESTS = 5  # requests


def rate_limiter(request: Request):
    """
    Rate limiting dependency to prevent brute force attacks.
    """
    client_ip = request.client.host
    current_time = time.time()

    if current_time - rate_limit_data[client_ip]["timestamp"] > RATE_LIMIT_DURATION:
        # Reset counter if duration has passed
        rate_limit_data[client_ip]["count"] = 1
        rate_limit_data[client_ip]["timestamp"] = current_time
    else:
        rate_limit_data[client_ip]["count"] += 1

    if rate_limit_data[client_ip]["count"] > RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
