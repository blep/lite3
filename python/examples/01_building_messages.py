from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys

def main():
    # Create buffer
    ctx = Lite3Buffer(initial_capacity=1024)
    
    # Build message
    root = ctx.init_obj()
    root["event"] = "lap_complete"
    root["lap"] = 55
    root["time_sec"] = 88.427
    
    print(f"buflen: {len(ctx.memory)}")
    print(f"Buffer (hex): {ctx.hex_dump()}")
    print(ctx.to_json_string())
    
    print("\nUpdating lap count")
    root["lap"] = 56
    
    print("Data to send:")
    print(f"buflen: {len(ctx.memory)}")
    print(f"Buffer (hex): {ctx.hex_dump()}")
    print(ctx.to_json_string())
    
    # Transmit: Copy buffer to rx (simulating network/copy)
    # The receiver initializes a new buffer with the received data
    rx_ctx = Lite3Buffer(data=ctx.memory)
    rx = rx_ctx.init_obj() # Root is at 0
    
    # Mutate rx
    print("\nVerifying fastest lap")
    rx["verified"] = "race_control"
    rx["fastest_lap"] = True
    
    print("Modified data:")
    print(f"rx_buflen: {len(rx_ctx.memory)}")
    print(f"Buffer (hex): {rx_ctx.hex_dump()}")
    print(rx_ctx.to_json_string())

if __name__ == "__main__":
    main()
