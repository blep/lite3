from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys

def main():
    ctx = Lite3Buffer()
    
    # Build message
    root = ctx.init_arr()
    root.append("zebra")
    root.append("giraffe")
    root.append("buffalo")
    root.append("lion")
    root.append("rhino")
    root.append("elephant")
    
    print(f"buflen: {len(ctx.memory)}")
    print(ctx.to_json_string())
    
    # Get element by index
    elem2 = root[2]
    print(f"Element at index 2: {elem2}")
    
    count = len(root)
    print(f"Element count: {count}")
    
    last = root[count - 1]
    print(f"Last element: {last}")
    
    print("\nOverwriting index 2 with \"gnu\"")
    root[2] = "gnu"
    
    print(f"buflen: {len(ctx.memory)}")
    print(ctx.to_json_string())

    print("\nOverwriting index 3 with \"springbok\"")
    root[3] = "springbok"
    print(f"buflen: {len(ctx.memory)}")
    print(ctx.to_json_string())

if __name__ == "__main__":
    main()
