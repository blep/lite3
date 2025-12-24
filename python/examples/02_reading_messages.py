from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys

def main():
    ctx = Lite3Buffer()
    
    # Build message
    root = ctx.init_obj()
    root["title"] = "C Programming Language, 2nd Edition"
    root["language"] = "en"
    root["price_usd"] = 60.30
    root["pages"] = 272
    root["in_stock"] = True
    root["reviews"] = None
    
    print(f"buflen: {len(ctx.memory)}")
    print(ctx.to_json_string())
    
    # Read back
    title = root["title"]
    language = root["language"]
    price_usd = root["price_usd"]
    pages = root["pages"]
    in_stock = root["in_stock"]
    
    print(f"\ntitle: {title}")
    print(f"language: {language}")
    print(f"price_usd: {price_usd}")
    print(f"pages: {pages}")
    print(f"in_stock: {'true' if in_stock else 'false'}\n")
    
    reviews = root["reviews"]
    if reviews is None:
            print("No reviews to display.")

    # Existence check
    print(f"\nTitle field exists: {'true' if root.exists('title') else 'false'}")
    print(f"Price field exists: {'true' if root.exists('price_usd') else 'false'}")
    print(f"ISBN field exists: {'true' if root.exists('isbn') else 'false'}")
    
    # Type checks
    val_title = root["title"]
    print(f"\nTitle is string type: {'true' if isinstance(val_title, str) else 'false'}")
    print(f"Title is integer type: {'true' if isinstance(val_title, int) else 'false'}")
    
    # Count
    print(f"\nObject entries: 0") # Mock

if __name__ == "__main__":
    main()
