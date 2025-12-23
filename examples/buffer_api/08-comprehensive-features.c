/*
    TRON (formerly known as Lite³): Tree Root Object Notation

    Copyright © 2025 Elias de Jong <elias@fastserial.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

      __ __________________        ____
    _  ___ ___/ /___(_)_/ /_______|_  /
     _  _____/ / __/ /_  __/  _ \_/_ < 
      ___ __/ /___/ / / /_ /  __/____/ 
           /_____/_/  \__/ \___/       
*/
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#include "lite3.h"


static unsigned char buf[4096]; // Larger buffer for complex structure

static void print_buffer(const unsigned char *p, size_t len)
{
        printf("Buffer (hex):");
        for (size_t i = 0; i < len; ++i) {
                if ((i % 4) == 0) printf(" ");
                printf("%02x", p[i]);
        }
        printf("\n");
}

int main() {
        size_t buflen = 0;
        size_t bufsz = sizeof(buf);
        size_t stats_ofs, inventory_ofs, spell_book_ofs, save_point_ofs, item_ofs, coords_ofs;

        // 1. Initialize Root Object (Character Profile)
        if (lite3_init_obj(buf, &buflen, bufsz) < 0) goto err;

        // 2. All Basic Data Types & Null
        if (lite3_set_str(buf, &buflen, 0, bufsz, "name", "Sir Bytealot") < 0) goto err;
        if (lite3_set_i64(buf, &buflen, 0, bufsz, "level", 60) < 0) goto err;
        if (lite3_set_f64(buf, &buflen, 0, bufsz, "hit_chance", 0.95) < 0) goto err;
        if (lite3_set_bool(buf, &buflen, 0, bufsz, "is_pvp_enabled", true) < 0) goto err;
        if (lite3_set_null(buf, &buflen, 0, bufsz, "guild") < 0) goto err;
        
        // Bytes type (simulated portrait data: 0xCAFEBABE)
        unsigned char portrait[] = { 0xCA, 0xFE, 0xBA, 0xBE };
        if (lite3_set_bytes(buf, &buflen, 0, bufsz, "portrait_raw", portrait, sizeof(portrait)) < 0) goto err;

        // 3. Edge Cases
        if (lite3_set_str(buf, &buflen, 0, bufsz, "nickname", "") < 0) goto err; // Empty string
        if (lite3_set_bytes(buf, &buflen, 0, bufsz, "custom_tag", NULL, 0) < 0) goto err; // Empty bytes
        
        // Empty Array
        size_t buffs_ofs;
        if (lite3_set_arr(buf, &buflen, 0, bufsz, "active_buffs", &buffs_ofs) < 0) goto err;
        // No items added to buffs -> empty array

        // Empty Object
        size_t pet_ofs;
        if (lite3_set_obj(buf, &buflen, 0, bufsz, "pet_stats", &pet_ofs) < 0) goto err;
        // No keys added to pet -> empty object


        // 4. Large Object (> Capacity) to force B-tree split
        // Adding 10 keys (Node capacity is 7)
        if (lite3_set_obj(buf, &buflen, 0, bufsz, "stats", &stats_ofs) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "str", 18) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "dex", 14) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "int", 10) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "vit", 16) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "wis", 12) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "cha", 8) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "agi", 13) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "luc", 9) < 0) goto err; // 8th key
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "end", 15) < 0) goto err; // 9th key
        if (lite3_set_i64(buf, &buflen, stats_ofs, bufsz, "per", 11) < 0) goto err; // 10th key


        // 5. Plain Array (Homogeneous)
        if (lite3_set_arr(buf, &buflen, 0, bufsz, "spell_book", &spell_book_ofs) < 0) goto err;
        if (lite3_arr_append_i64(buf, &buflen, spell_book_ofs, bufsz, 101) < 0) goto err; // Fireball ID
        if (lite3_arr_append_i64(buf, &buflen, spell_book_ofs, bufsz, 205) < 0) goto err; // Icebolt ID
        if (lite3_arr_append_i64(buf, &buflen, spell_book_ofs, bufsz, 303) < 0) goto err; // Heal ID


        // 6. Object Array (Inventory with Typed Items)
        if (lite3_set_arr(buf, &buflen, 0, bufsz, "inventory", &inventory_ofs) < 0) goto err;
        
        // Item 1: Weapon
        if (lite3_arr_append_obj(buf, &buflen, inventory_ofs, bufsz, &item_ofs) < 0) goto err;
        if (lite3_set_str(buf, &buflen, item_ofs, bufsz, "type", "weapon") < 0) goto err;
        if (lite3_set_str(buf, &buflen, item_ofs, bufsz, "name", "Rusty Sword") < 0) goto err;
        if (lite3_set_i64(buf, &buflen, item_ofs, bufsz, "dmg", 5) < 0) goto err;

        // Item 2: Potion
        if (lite3_arr_append_obj(buf, &buflen, inventory_ofs, bufsz, &item_ofs) < 0) goto err;
        if (lite3_set_str(buf, &buflen, item_ofs, bufsz, "type", "potion") < 0) goto err;
        if (lite3_set_str(buf, &buflen, item_ofs, bufsz, "name", "Healing Potion") < 0) goto err;
        if (lite3_set_i64(buf, &buflen, item_ofs, bufsz, "heal", 50) < 0) goto err;


        // 7. Mixed-Type Array (Tuple: Zone, Timestamp, Coordinates)
        if (lite3_set_arr(buf, &buflen, 0, bufsz, "save_point", &save_point_ofs) < 0) goto err;
        
        // Element 0: Zone Name (String)
        if (lite3_arr_append_str(buf, &buflen, save_point_ofs, bufsz, "Dark Forest") < 0) goto err;
        
        // Element 1: Timestamp (Integer)
        if (lite3_arr_append_i64(buf, &buflen, save_point_ofs, bufsz, 1734900000) < 0) goto err;
        
        // Element 2: Coordinates (Nested Object)
        if (lite3_arr_append_obj(buf, &buflen, save_point_ofs, bufsz, &coords_ofs) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, coords_ofs, bufsz, "x", 120) < 0) goto err;
        if (lite3_set_i64(buf, &buflen, coords_ofs, bufsz, "y", 55) < 0) goto err;


        // Output
        printf("--- Lite3 Comprehensive Binary Format Dump ---\n");
        printf("Total Size: %zu bytes\n", buflen);
        print_buffer(buf, buflen);
        
        printf("\n--- JSON Validation ---\n");
        if (lite3_json_print(buf, buflen, 0) < 0) { // Print Lite³ as JSON
                perror("Failed to print JSON");
                return 1;
        }
        printf("\n");

        return 0;

err:
        perror("Failed to build message");
        return 1;
}
