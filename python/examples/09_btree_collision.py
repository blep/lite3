import sys
import os

# Add the 'python' directory to sys.path to allow importing the lite3 package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lite3

def print_hex_dump(data):
    hex_str = data.hex()
    output = []
    for i in range(0, len(hex_str), 8):
        chunk = hex_str[i:i+8]
        # split into bytes
        bytes_list = [chunk[j:j+2] for j in range(0, len(chunk), 2)]
        output.append(" ".join(bytes_list))
    print("Buffer (hex):" + "".join(output))

def main():
    # 128 keys that all share the same DJB2 hash (collision)
    # Target Hash (DJB2 "test"): 2090756197
    colliding_keys = [
        "Hw0QbwxPkYhT", "KLAXLx3ba62o", "HRHdPT5Fp27C", "9j7idIKf1g6R",
        "lqWwe4YB7re4", "Lqvh1SesMp9T", "6weJ9bqhxq2v", "LKgKzPLHKKRr",
        "kji2CuAGq493", "cFElGOVX0WEW", "Sm7u4aV4jlSm", "M4hpZY1nocWm",
        "0hPLYykBye9w", "V0fpx9VVNZYg", "TtCoRFcqa0t6", "VUxuQi7pTAAR",
        "v45oYd5lP1dP", "5KY9KD60UjDw", "kjNYVShynr7d", "M8Dj5RdtL1ii",
        "mZGyOaMw0NPx", "PeGTlfwydhsP", "d0XQ7VN1G1uk", "F7Ie8jljeL4y",
        "tEDxaenM6Or4", "qz1qhbbKikTu", "j6ppPzsONGi7", "uq6XvW6kIOst",
        "2HV28WJO6sTZ", "1oNadxSXjIpH", "8PQsp1Baxxlu", "a81Cir9z876A",
        "0ZXF1hazWpOO", "EJEHww5tjkc6", "8PxCb1RbXbjS", "yB1jurcrlXFe",
        "b6YyJ409IKiS", "awPX2Oi3i0XS", "16xWkWWtCMAM", "RIFyitrOjkAs",
        "nQlA1v4aLhUP", "xTeXjXuMACiG", "hvtupVsAsCXr", "CPEdTxoI5hzj",
        "pnKIRVqhpffR", "TijM29fnxTQQ", "HBVveY9RoSQO", "bLhEZ6qGN9a6",
        "24zGeW0Vu67V", "D3MXLzrYBgcH", "hpVGC3DoW1RI", "9ivft2PUlbzP",
        "66gnBu45jBd0", "Zz1jbVE2TaIE", "YjLJsmK7KyvL", "eOTDKqTJJZSD",
        "hSnEoK1F4XeQ", "L90Tl35GqbVt", "6c8XZxPBikku", "9k4BQg4VNpZM",
        "vcbb9xOsE5BU", "e29HRrNeAmWm", "ln0S6DfSo6x4", "ADS6se2V7UTs",
        "2Uu83ENHyILQ", "DScDeElb2ADT", "LCd0KIIf4YkC", "KH2EvxIryYrj",
        "0U1ZQnJbBCKV", "MbKTwznTgClj", "QssmjxkO1kCB", "gPvBpDDJyPox",
        "8gFO5UXXW37r", "GAUFsv27cvLg", "de3dFZlQpExw", "i36gtO9MUQnK",
        "EPQ864ANohji", "PATByORh6H4F", "TkeGFQr3kyKK", "HYFupwujrplq",
        "80IS0Vbs1rUJ", "P8T1PmlvfKMw", "mWtImPZwpzR6", "bX536Y3eiCIC",
        "ThyYNkaZOQLs", "FR1JsxfV1caR", "HKsr9jLCKzyY", "DhmiN76MFKvP",
        "kTILgxBIj93m", "MbRQ0cLfMruV", "TwSl9YYpOl01", "GL74IqFqGq5E",
        "a2Z5wfuV8ISc", "fmX6JZxDPe56", "KrIMGlTuHvGm", "RUe33Ezer5mw",
        "hkJiDJyuNmM7", "27HC0ikwrkrc", "Gs2Q8ZYipDrJ", "VLkQqdRogdhz",
        "iC4js1X2XmSQ", "O8MJB5KCjSzG", "Dit3Agn5okCe", "LF6HBUBsvEqY",
        "hzWWAlZpH4nP", "BLtRJ5zCH5B2", "kZ9ZUK6k58Za", "mdMY53VzloqF",
        "uQPcq26X8Xbe", "xgs5M0IHpYYJ", "RZo32hRhJIEG", "oJpEPBw7T2wv",
        "r8lFJPYcuVvN", "7WZYuVxfPiDZ", "OaK3WOE0NEUp", "WEHbFIZxAYH8",
        "inP1fVSYunnP", "E9vwy9lYeuTQ", "hmB0R0qUgJgz", "suTQG6Xekio7",
        "OSv4OJJ1Vlfy", "0I7cAC0MBptG", "CETJ4gkYLd39", "45Pgx0ZunkoB",
        "E0J30Bl1FeIL", "8VWFgLt3vpUa", "nhDDBAnoTNgZ", "FUktWhlqCkYd"
    ]
    
    # Create Lite3 Buffer and Initialize Root Object
    buf = lite3.Lite3Buffer(initial_capacity=16384)
    obj = buf.init_obj()
    
    # Insert keys
    for i, key in enumerate(colliding_keys):
        obj[key] = i
        
    print("--- Lite3 Comprehensive Binary Format Dump ---")
    data = buf.memory.tobytes()
    print(f"Total Size: {len(data)} bytes")
    print_hex_dump(data)
    
    print("\n--- JSON Validation ---")
    # Python Lite3 implementation doesn't have a direct .json() method on the object yet in core.py
    # We can rely on standard json library and internal dict conversion if available,
    # or just print the key-value pairs manually for validation.
    # Checking core.py, there isn't a recursive to_dict or json helper exposed easily on Lite3Object.
    # Let's iterate and print manually to prove retrieval works.
    
    import json
    
    output_dict = {}
    for k in obj:
        output_dict[k] = obj[k]
        
    print(json.dumps(output_dict, indent=4))

if __name__ == "__main__":
    main()
