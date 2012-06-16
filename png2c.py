#!/usr/bin/python2.7
import sys
import png
import curses.ascii

if len(sys.argv) < 2:
    sys.stderr.write("Please specify the input PNG file\n")
    sys.exit(1)

reader = png.Reader(filename=sys.argv[1])
data = reader.asRGB()
size = data[:2] # get image width and height
char_size = (size[0] / 16, size[1] / 16) # 16 characters in a row, 16 rows of characters
bitmap = list(data[2]) # get image RGB values

sys.stdout.write("""#include "font.h"

#if 0
#ifndef FONT_H_
#define FONT_H_

typedef struct {
    unsigned char_width;
    unsigned char_height;
    const char * font_name;
    unsigned char first_char;
    unsigned char last_char;
    unsigned char * font_bitmap;
} font_t;

extern const font_t console_fonts[];

#endif /* FONT_H_ */
#endif
""")

sys.stdout.write("""unsigned char console_font_%dx%d[] = {
""" % char_size)

raster = []
for line in bitmap:
    raster.append([c == 255 and 1 or 0 for c in [line[k+1] for k in range(0, size[0] * 3, 3)]])

# array of character bitmaps; each bitmap is an array of lines, each line
# consists of 1 - bit is set and 0 - bit is not set
char_bitmaps = [] 
for c in range(256): # for each character
    char_bitmap = []
    raster_row = (c / 16) * char_size[1]
    offset = (c % 16) * char_size[0]
    for y in range(char_size[1]): # for each scan line of the character
        char_bitmap.append(raster[raster_row + y][offset : offset + char_size[0]])
    char_bitmaps.append(char_bitmap)
raster = None # no longer required

# how many bytes a single character scan line should be
num_bytes_per_scanline = (char_size[0] + 7) / 8

# convert the whole bitmap into an array of character bitmaps
char_bitmaps_processed = []
for c in range(len(char_bitmaps)):
    bitmap = char_bitmaps[c]
    encoded_lines = []
    for line in bitmap:
        encoded_line = []
        for b in range(num_bytes_per_scanline):
            offset = b * 8
            char_byte = 0
            mask = 0x80
            for x in range(8):
                if b * 8 + x >= char_size[0]:
                    break
                if line[offset + x]:
                    char_byte += mask
                mask >>= 1
            encoded_line.append(char_byte)
        encoded_lines.append([encoded_line, line])
    char_bitmaps_processed.append([c, encoded_lines])
char_bitmaps = None

for c in char_bitmaps_processed:
    sys.stdout.write("""
    /*
     * code=%d, hex=0x%02X, ascii="%s"
     */
""" % (c[0], c[0], curses.ascii.unctrl(c[0])))
    for line in c[1]:
        sys.stdout.write("    ")
        for char_byte in line[0]:
            sys.stdout.write(("0x%02X," % char_byte))
        sys.stdout.write("  /* %s */" % ''.join([str(s) for s in line[1]]))
        sys.stdout.write("\n")

sys.stdout.write("""};

""")
