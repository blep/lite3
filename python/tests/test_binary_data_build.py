import pytest
from lite3 import Lite3Buffer
import binascii

def assert_hex_equal(actual_hex: str, expected_hex: str):
    """
    Compares two hex strings and reports the first mismatch with offset details.
    Ignores whitespace in hex strings.
    """
    # Normalize: lower case and remove spaces
    actual = actual_hex.lower().replace(" ", "").replace("\n", "")
    expected = expected_hex.lower().replace(" ", "").replace("\n", "")
    
    # Convert to bytes for byte-aligned comparison (optional, but cleaner for display)
    # If the hex string definition itself is invalid (odd length), this might fail
    # but we assume valid hex.
    
    if actual == expected:
        return

    # Find mismatch
    min_len = min(len(actual), len(expected))
    diff_index = -1
    
    # Compare by hex char (nibble) first to find index
    for i in range(min_len):
        if actual[i] != expected[i]:
            diff_index = i
            break
            
    if diff_index == -1:
        # One is a prefix of the other
        diff_index = min_len
        msg = f"Length mismatch: Actual {len(actual)} vs Expected {len(expected)}. Identical up to char {min_len}."
    else:
        # Byte index is char index // 2
        byte_offset = diff_index // 2
        
        # Get context (16 bytes before and after)
        # 32 chars before, 32 chars after
        start = max(0, diff_index - 32)
        end = min(min_len, diff_index + 32)
        
        context_actual = actual[start:end]
        context_expected = expected[start:end]
        
        # Pointer string to highlight diff
        # diff_index relative to start
        pointer_pos = diff_index - start
        pointer = " " * pointer_pos + "^"
        
        msg = (
            f"Binary mismatch at byte offset {byte_offset} (char offset {diff_index})\n"
            f"Expected: ...{context_expected}...\n"
            f"Actual:   ...{context_actual}...\n"
            f"             {pointer}\n"
            f"Expected byte: {expected[byte_offset*2:byte_offset*2+2] if byte_offset*2+1 < len(expected) else 'EOF'}\n"
            f"Actual byte:   {actual[byte_offset*2:byte_offset*2+2] if byte_offset*2+1 < len(actual) else 'EOF'}"
        )

    raise AssertionError(msg)

class TestBinaryDataBuild:
    """
    Tests determining if the Python implementation produces the exact same binary 
    layout as the C implementation for specific build scenarios.
    """

    def test_example_1_simple_build(self):
        """
        Reproduces the initial build phase of examples/buffer_api/01-building-messages.c
        and compares the binary output.
        """
        # Expected Hex (from 01-building-messages-output.txt, first dump)
        # 154 bytes
        # Expected Hex (from 01-building-messages-output.txt)
        expected_hex = (
            "06030000428b880b071c650f2eb1c62100000000000000000000000000000000"
            "c300000079000000600000008700000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "186576656e740005"
            "0d0000006c61705f636f6d706c65746500106c6170000237"
            "000000000000002474696d655f736563000317d9cef7531b5640"
        )

        # Build Logic
        ctx = Lite3Buffer(initial_capacity=1024)
        root = ctx.init_obj()
        # Note: Order matters for binary layout if implementation is consistent
        # C example: event, lap, time_sec
        root["event"] = "lap_complete"
        root["lap"] = 55
        root["time_sec"] = 88.427

        # Verification
        assert_hex_equal(ctx.hex_dump(), expected_hex)


    def test_example_8_complex_build(self):
        """
        Reproduces the build phase of examples/buffer_api/08-comprehensive-features.c
        and compares the binary output.
        """
        # Expected Hex (from 08-comprehensive-features-output.txt)
        # 1900 bytes. 
        # CAUTION: The C dump output usually adds spaces. We remove them.
        expected_hex = (
            "060e00008076706a000000000000000000000000000000000000000000000000"
            "810300009d000000000000000000000000000000000000000000000000000000"
            "e000000040010000000000000000000000000000000000000000000000000000"
            "146e616d6500050d0000005369722042797465616c6f7400186c6576656c0002"
            "3c000000000000002c6869745f6368616e63650003666666666666ee3f3c6973"
            "5f7076705f656e61626c6564000101186775696c64000034706f727472616974"
            "5f726177000404000000cafebabe246e69636b6e616d65000501000000000000"
            "060800005ad1880f3dbcda0f144a61101bec70102bec332e96cf623ddd716954"
            "07000000af000000780000008d020000a001000088000000b20100006c060000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "06000000460c9b7ccb9e5c8103abde88f36f69ac8fff44affcdce6e500000000"
            "0600000060000000ce000000b7000000cd040000440400002102000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "2c637573746f6d5f74616700040000000000346163746976655f627566667300"
            "0700000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000000000000000000000287065"
            "745f737461747300060000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000000000000000000000187374"
            "61747300060a00003080880b0000000000000000000000000000000000000000"
            "8102000010030000000000000000000000000000000000000000000058030000"
            "b803000000000000000000000000000000000000000000000000000010737472"
            "000212000000000000001064657800020e0000000000000010696e7400020a00"
            "00000000000010766974000210000000000000001077697300020c0000000000"
            "000010636861000208000000000000001061676900020d000000000000000608"
            "0000365d880bd165880bc669880b1c6f880b0000000000000000000000000400"
            "0000480300003a03000002030000260400000000000000000000000000000000"
            "000000000000000000000000000000000000000006000000c98d880bcc9c880b"
            "7eab880bd8b6880b18bb880b0000000000000000050000001804000034040000"
            "f40200001e0300002c0300000000000000000000000000000000000000000000"
            "00000000000000000000000000000000106c7563000209000000000000001065"
            "6e6400020f000000000000001070657200020b000000000000002c7370656c6c"
            "5f626f6f6b000703000000000000010000000200000000000000000000000000"
            "000000000000c3000000b0040000b9040000c204000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000002650000"
            "000000000002cd00000000000000022f010000000000000028696e76656e746f"
            "7279000702000000000000010000000000000000000000000000000000000082"
            "00000038050000d0050000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000006030000bd6a880b460c9b7c"
            "07bd9e7c00000000000000000000000000000000c3000000c1050000aa050000"
            "9805000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000001474797065000507000000776561706f6e00146e"
            "616d6500050c00000052757374792053776f72640010646d6700020500000000"
            "000000060300007fd1977c460c9b7c07bd9e7c00000000000000000000000000"
            "000000c30000005c060000420600003006000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000001474797065000507"
            "000000706f74696f6e00146e616d6500050f0000004865616c696e6720506f74"
            "696f6e00146865616c000232000000000000002c736176655f706f696e740007"
            "03000000000000010000000200000000000000000000000000000000000000c3"
            "000000d8060000e9060000f40600000000000000000000000000000000000000"
            "00000000000000000000000000000000000000050c0000004461726b20466f72"
            "6573740002207968670000000000060200001db602001eb60200000000000000"
            "0000000000000000000082000000540700006007000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000008780002"
            "7800000000000000087900023700000000000000"
        )
        ctx = Lite3Buffer(initial_capacity=4096)

        # 1. Initialize Root Object (Character Profile)
        root = ctx.init_obj()

        # 2. All Basic Data Types & Null
        root["name"] = "Sir Bytealot"
        root["level"] = 60
        root["hit_chance"] = 0.95
        root["is_pvp_enabled"] = True
        root["guild"] = None
        
        # Bytes type (simulated portrait data: 0xCAFEBABE)
        root["portrait_raw"] = b'\xCA\xFE\xBA\xBE'

        # 3. Edge Cases
        root["nickname"] = ""
        root["custom_tag"] = b"" # Empty bytes

        # Empty Array
        root.create_array("active_buffs")
        # No items added

        # Empty Object
        root.create_object("pet_stats")
        # No keys added

        # 4. Large Object (> Capacity) to force B-tree split
        # Adding 10 keys (Node capacity is 7)
        stats = root.create_object("stats")
        stats["str"] = 18
        stats["dex"] = 14
        stats["int"] = 10
        stats["vit"] = 16
        stats["wis"] = 12
        stats["cha"] = 8
        stats["agi"] = 13
        stats["luc"] = 9
        stats["end"] = 15
        stats["per"] = 11

        # 5. Plain Array (Homogeneous)
        spell_book = root.create_array("spell_book")
        spell_book.append(101)
        spell_book.append(205)
        spell_book.append(303)

        # 6. Object Array (Inventory with Typed Items)
        inventory = root.create_array("inventory")
        
        # Item 1: Weapon
        item1 = inventory.append_object()
        item1["type"] = "weapon"
        item1["name"] = "Rusty Sword"
        item1["dmg"] = 5

        # Item 2: Potion
        item2 = inventory.append_object()
        item2["type"] = "potion"
        item2["name"] = "Healing Potion"
        item2["heal"] = 50

        # 7. Mixed-Type Array (Tuple: Zone, Timestamp, Coordinates)
        save_point = root.create_array("save_point")
        
        # Element 0: Zone Name (String)
        save_point.append("Dark Forest")
        
        # Element 1: Timestamp (Integer)
        save_point.append(1734900000)
        
        # Element 2: Coordinates (Nested Object)
        coords = save_point.append_object()
        coords["x"] = 120
        coords["y"] = 55

        # Verification
        assert_hex_equal(ctx.hex_dump(), expected_hex)
