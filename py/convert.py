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
                                        ).convert('YCbCr')
    im_data = im.getdata()
    data_y = [y for (y, cb, cr) in im_data]
    data_cb = [cb for (y, cb, cr) in im_data]
    data_cr = [cr for (y, cb, cr) in im_data]

    image_y = deserial_x(data_y, im.width)
    image_cb = deserial_x(data_cb, im.width)
    image_cr = deserial_x(data_cr, im.width)

    reduced_cb = [[int((image_cb[y][x] + image_cb[y][x+1] + image_cb[y+1][x] + image_cb[y+1][x+1]) / 4)
                   for x in range(0, im.width, 2)] for y in range(0, im.height, 2)]

    reduced_cr = [[int((image_cr[y][x] + image_cr[y][x+1] + image_cr[y+1][x] + image_cr[y+1][x+1]) / 4)
                   for x in range(0, im.width, 2)] for y in range(0, im.height, 2)]

    serial_y = serial_x(image_y)
    serial_cb = serial_x(reduced_cb)
    serial_cr = serial_x(reduced_cr)

    return serial_y + serial_cb + serial_cr


f_start = 24 * 40
f_end = 24 * 41


def main():
    start = datetime.now()
    tbar = Bar("Converting images..", max=(f_end - f_start))
    frames = range(f_start, f_end)
    fileout = open("streams/ycbcr.bin", "wb")
    for frame in frames:
        fileout.write(bytes(process("frames/{0:05d}.png".format(frame))))
        tbar.next()
    tbar.finish()
    fileout.close()
    print("Took ", datetime.now() - start)


if __name__ == "__main__":
    main()
