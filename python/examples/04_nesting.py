from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys

def main():
    ctx = Lite3Buffer()
    
    root = ctx.init_obj()
    root["event"] = "http_request"
    root["method"] = "POST"
    root["duration_ms"] = 47
    
    # Nested object
    headers = root.create_object("headers")
    headers["content-type"] = "application/json"
    headers["x-request-id"] = "req_9f8e2a"
    headers["user-agent"] = "curl/8.1.2"
    
    print(ctx.to_json_string())
    
    # Read nested
    ua = root["headers"]["user-agent"]
    print(f"User agent: {ua}")

if __name__ == "__main__":
    main()
