from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys

def main():
    ctx = Lite3Buffer()
    
    root = ctx.init_obj()
    root["name"] = "Marie"
    root["age"] = 24
    root["email"] = "marie@example.com"
    
    # Get string
    email = root["email"]
    
    # In Python, 'email' is a string object, so modifying the buffer 
    # doesn't affect this variable.
    root["phone"] = "1234567890"
    
    print(f"Marie's email: {email}\n")
    
    country = "Germany"
    root["country"] = country
    
    print(ctx.to_json_string())

if __name__ == "__main__":
    main()
