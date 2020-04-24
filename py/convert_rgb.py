from progress.bar import Bar
from PIL import Image
from datetime import datetime


def serial_x(arr):
    return [arr[y][x] for y in range(len(arr)) for x in range(len(arr[0]))]


def deserial_x(arr, width):
    height = int(len(arr) / width)
    return [[arr[y * width + x] for x in range(width)] for y in range(height)]


def get_block(arr, y, x, size):
    return [[arr[size * y + yi][size * x + xi] for yi in range(size)] for xi in range(size)]


def process(image_path):
    im: Image.Image = Image.open(image_path
                                 ).crop((144, 60, 496, 300)
                                        )
    im_data = im.getdata()
    data_xx = deserial_x(im_data, im.width)
    output = []

    for blk_y in range(int(im.height / 8)):
        for blk_x in range(int(im.width / 8)):
            blk = get_block(data_xx, blk_y, blk_x, 8)
            blk_ser = serial_x(blk)
            for (r, g, b) in blk_ser:
                output.append((b << 16) + (g << 8) + r)

    return str().join(["24'h{0:06x}\n".format(x) for x in output])


f_start = 24 * 40
f_end = 24 * 41

# Single frame for testing
# f_start = 1107
# f_end = 1107


def main():
    start = datetime.now()
    tbar = Bar("Converting images..", max=(f_end - f_start))
    frames = range(f_start, f_end)
    fileout = open("streams/rgb.txt", "w")
    for frame in frames:
        fileout.write(process("frames/{0:05d}.png".format(frame)))
        tbar.next()
    tbar.finish()
    fileout.close()
    print("Took ", datetime.now() - start)


if __name__ == "__main__":
    main()
