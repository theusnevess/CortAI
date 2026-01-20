import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000/observe"

event = {
    "event_type": "VIDEO_PERFORMANCE_SNAPSHOT",
    "platform": "tiktok",
    "video_id": "721983712983",
    "timestamp": datetime.utcnow().isoformat(),
    "metrics": {
        "views": 143,
        "likes": 3,
        "comments": 0,
        "shares": 0
    },
    "raw_payload": {
        "caption": "testando um formato novo",
        "hashtags": ["#fyp", "#teste"],
        "duration_seconds": 14
    }
}

response = requests.post(API_URL, json=event)
print(response.status_code, response.json())
