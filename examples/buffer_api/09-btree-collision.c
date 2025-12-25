/*
    Lite3 Example 9: B-tree Hash Collisions
    
    This example demonstrates the robustness of the Lite3 B-tree implementation
    by inserting 128 keys that all produce the same DJB2 hash (collision).
    Lite3 should handle this gracefully by using its collision resolution strategy
    (linear probing and node splitting).
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "lite3.h"

// Large buffer to accommodate 128 entries + split nodes
// Each entry ~ 12 bytes key + 8 bytes value + overhead -> 20-30 bytes.
// 128 * 30 = 3840. Plus nodes. 16KB should be plenty.
static unsigned char buf[16384];

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
    
    // 128 colliding keys (Target Hash: 2090756197)
    const char *keys[] = {
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
    };

    if (lite3_init_obj(buf, &buflen, bufsz) < 0) {
        perror("Failed to init object");
        return 1;
    }

    for (int i = 0; i < 128; i++) {
        if (lite3_set_i64(buf, &buflen, 0, bufsz, keys[i], i) < 0) {
            fprintf(stderr, "Failed to set key %d: %s\n", i, keys[i]);
            return 1;
        }
    }

    printf("--- Lite3 Comprehensive Binary Format Dump ---\n");
    printf("Total Size: %zu bytes\n", buflen);
    print_buffer(buf, buflen);
    
    printf("\n--- JSON Validation ---\n");
    if (lite3_json_print(buf, buflen, 0) < 0) {
            perror("Failed to print JSON");
            return 1;
    }
    printf("\n");

    return 0;
}
