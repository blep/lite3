import pytest
from lite3 import Lite3Buffer
import json
import base64

def assert_json_equal(actual_json_str: str, expected_json_str: str):
    """
    Parses both JSON strings, normalizes them (sort keys), and asserts equality.
    """
    try:
        actual_obj = json.loads(actual_json_str)
    except json.JSONDecodeError as e:
        pytest.fail(f"Actual JSON failed to decode: {e}\nContent: {actual_json_str}")

    try:
        expected_obj = json.loads(expected_json_str)
    except json.JSONDecodeError as e:
        pytest.fail(f"Expected JSON failed to decode: {e}\nContent: {expected_json_str}")
        
    # Helper to decode base64 strings if needed? 
    # The C output uses base64 for bytes? "portrait_raw": "yv66vg=="
    # Our python implementation to_json_string likely should do the same.
    # Python's default json dump doesn't handle bytes, we must handle it in our custom encoder.
    
    # We compare the structural equality which is robust against spacing/indentation differences
    assert actual_obj == expected_obj

class TestBinaryDataToJson:
    """
    Tests converting raw Lite3 binary data (from known C output) back to JSON.
    This validates the reading/parsing logic of the Python implementation.
    """

    def test_example_1_to_json(self):
        # Hex dumped from C working example 01 (first dump)
        # Hex dumped from C working example 01 (Building Messages Phase)
        hex_data = (
            "06030000428b880b071c650f2eb1c62100000000000000000000000000000000"
            "c300000079000000600000008700000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "186576656e7400050d0000006c61705f636f6d706c65746500106c6170000237"
            "000000000000002474696d655f736563000317d9cef7531b5640"
        )
        data = bytes.fromhex(hex_data)
        
        # Expected JSON from 01-building-messages-output.txt
        expected_json = """
        {
            "event": "lap_complete",
            "lap": 55,
            "time_sec": 88.427
        }
        """
        
        # Initialize buffer with raw data
        ctx = Lite3Buffer(data=data)
        
        # Convert to JSON
        json_out = ctx.to_json_string()
        
        # assertions
        assert_json_equal(json_out, expected_json)

    def test_example_8_to_json(self):
        # Hex dumped from C working example 08
        hex_data = (
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
            "0000000000000000000000000000000000000000000000000000000000000000"
            "00287065745f7374617473000600000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000018737461747300060a00003080880b00000000"
            "0000000000000000000000000000000000000000810200001003000000000000"
            "000000000000000000000000000000000000000058030000b803000000000000"
            "0000000000000000000000000000000000000000107374720002120000000000"
            "00001064657800020e0000000000000010696e7400020a000000000000001076"
            "6974000210000000000000001077697300020c00000000000000106368610002"
            "08000000000000001061676900020d00000000000000000006080000365d880b"
            "d165880bc669880b1c6f880b0000000000000000000000000400000048030000"
            "3a03000002030000260400000000000000000000000000000000000000000000"
            "00000000000000000000000000000000000000000000000006000000c98d880b"
            "cc9c880b7eab880bd8b6880b18bb880b00000000000000000500000018040000"
            "34040000f40200001e0300002c03000000000000000000000000000000000000"
            "000000000000000000000000000000000000000000000000106c756300020900"
            "00000000000010656e6400020f000000000000001070657200020b0000000000"
            "000000002c7370656c6c5f626f6f6b0007030000000000000100000002000000"
            "00000000000000000000000000000000c3000000b0040000b9040000c2040000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000002650000000000000002cd0000000000"
            "0000022f01000000000000000028696e76656e746f7279000702000000000000"
            "0100000000000000000000000000000000000000000000008200000038050000"
            "d005000000000000000000000000000000000000000000000000000000000000"
            "00000000000000000000000000000000000000000000000006030000bd6a880b"
            "460c9b7c07bd9e7c00000000000000000000000000000000c3000000c1050000"
            "aa05000098050000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000001474797065000507"
            "000000776561706f6e00146e616d6500050c00000052757374792053776f7264"
            "0010646d670002050000000000000000060300007fd1977c460c9b7c07bd9e7c"
            "00000000000000000000000000000000c30000005c0600004206000030060000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000001474797065000507000000706f74696f"
            "6e00146e616d6500050f0000004865616c696e6720506f74696f6e0014686561"
            "6c00023200000000000000002c736176655f706f696e74000703000000000000"
            "010000000200000000000000000000000000000000000000c3000000d8060000"
            "e9060000f4060000000000000000000000000000000000000000000000000000"
            "000000000000000000000000000000000000000000000000050c000000446172"
            "6b20466f72657374000220796867000000000000060200001db602001eb60200"
            "0000000000000000000000000000000000000000820000005407000060070000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000087800027800000000000000"
            "087900023700000000000000"
        )
        data = bytes.fromhex(hex_data)

        # Expected JSON from 08-comprehensive-output.txt
        expected_json = """
        {
            "guild": null,
            "level": 60,
            "stats": {
                "agi": 13,
                "cha": 8,
                "dex": 14,
                "end": 15,
                "int": 10,
                "luc": 9,
                "per": 11,
                "str": 18,
                "vit": 16,
                "wis": 12
            },
            "custom_tag": "",
            "hit_chance": 0.95,
            "active_buffs": [],
            "save_point": [
                "Dark Forest",
                1734900000,
                {
                    "x": 120,
                    "y": 55
                }
            ],
            "is_pvp_enabled": true,
            "name": "Sir Bytealot",
            "nickname": "",
            "portrait_raw": "yv66vg==",
            "inventory": [
                {
                    "dmg": 5,
                    "name": "Rusty Sword",
                    "type": "weapon"
                },
                {
                    "heal": 50,
                    "name": "Healing Potion",
                    "type": "potion"
                }
            ],
            "spell_book": [
                101,
                205,
                303
            ],
            "pet_stats": {}
        }
        """
        
        ctx = Lite3Buffer(data=data)
        
        # Convert to JSON
        json_out = ctx.to_json_string()
        
        # assertions
        assert_json_equal(json_out, expected_json)
