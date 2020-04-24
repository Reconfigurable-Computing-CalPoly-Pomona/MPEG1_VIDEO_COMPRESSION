import math
from progress.bar import Bar
from datetime import datetime

filein = open("streams/ycbcr.bin", "rb")
fileout = open("streams/compressed.bin", "wb")

im_w = 352
im_h = 240
frames = 24 * 20

qy = [
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
]

qc = [
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
]

zzp = []
for s1 in range(8):
    for s2 in range(s1 + 1):
        if s1 % 2 == 0:
            zzp.append((s1 - s2, s2))
        else:
            zzp.append((s2, s1 - s2))
zzp = zzp[:-4]
zzp += [(7-y, 7-x) for (y, x) in zzp[::-1]]


def serial_x(arr):
    return [arr[y][x] for y in range(len(arr)) for x in range(len(arr[0]))]


def deserial_x(arr, width):
    height = int(len(arr) / width)
    return [[arr[y * width + x] for x in range(width)] for y in range(height)]


def zigzag_8(arr):
    return [arr[y][x] for (y, x) in zzp]


def read_frame():
    data_y = deserial_x(filein.read(im_w * im_h), im_w)
    data_cb = deserial_x(filein.read(int(im_w / 2 * im_h / 2)), int(im_w/2))
    data_cr = deserial_x(filein.read(int(im_w / 2 * im_h / 2)), int(im_w/2))
    return (data_y, data_cb, data_cr)


def get_block(arr, y, x, size):
    return [[arr[size * y + yi][size * x + xi] for yi in range(size)] for xi in range(size)]


def dct(block):
    m = 8
    n = 8
    output = [[0 for _ in range(n)] for _ in range(m)]
    for i in range(m):
        for j in range(n):
            if i == 0:
                ci = 1 / math.sqrt(m)
            else:
                ci = math.sqrt(2) / math.sqrt(m)

            if j == 0:
                cj = 1 / math.sqrt(n)
            else:
                cj = math.sqrt(2) / math.sqrt(n)

            dctsum = 0
            for k in range(m):
                for l in range(n):
                    dct1 = block[k][l] * math.cos((2 * k + 1) * i * math.pi / (
                        2 * m)) * math.cos((2 * l + 1) * j * math.pi / (2 * n))
                    dctsum = dctsum + dct1
            output[i][j] = ci * cj * dctsum

    return output


def quantize(block, coef):
    return [[int(block[y][x] / coef[y][x]) for y in range(8)] for x in range(8)]


def subtract(block, const):
    return [[int(block[y][x] - const) for y in range(8)] for x in range(8)]


def process_block(block, coef):
    return quantize(dct(subtract(block, 128)), coef)


def huffman(array):
    code_freq = {}
    for val in array:
        if val in code_freq:
            code_freq[val] += 1
        else:
            code_freq[val] = 1

    if(len(code_freq) > 16):
        raise Exception("Not enough bits for length")

    def make_vals(freqs):
        left = freqs[0][0]
        right = freqs[0][1]
        ret = []

        if(type(left[0]) is tuple):
            ret += [(1 + a, b + 2**a, c) for (a, b, c) in make_vals(left)]
        else:
            ret += [(1, 1, left[0])]

        if(type(right[0]) is tuple):
            ret += [(1 + a, b, c) for (a, b, c) in make_vals(right)]
        else:
            ret += [(1, 0, right[0])]

        return ret

    new_freqs = [(num, code_freq[num]) for num in code_freq]

    encoder = {}

    if len(new_freqs) == 1:
        encoder[new_freqs[0][0]] = (1, 0)
    else:
        while len(new_freqs) > 1:
            new_freqs.sort(key=lambda x: x[1])
            left = new_freqs[0]
            del new_freqs[0]
            right = new_freqs[0]
            del new_freqs[0]
            new_freqs.append(((left, right), left[1] + right[1]))

        nf = new_freqs[0]

        for (bits, num, val) in make_vals(nf):
            encoder[val] = (bits, num)

    bits = 0
    num = 0
    for val in array:
        (b, n) = encoder[val]
        bits += b
        num <<= b
        num += n

    e_req = math.ceil(math.log2(encoder[max(encoder, key=encoder.get)][0]))
    bits_e = 8
    num_e = len(encoder) << 4 + e_req

    for value in encoder:
        b, n = encoder[value]
        bits_e += e_req
        num_e <<= e_req
        num_e += b

        bits_e += b
        num_e <<= b
        num_e += n

        bits_e += 8
        num_e <<= 8
        bits_e += n

    raise_bits_e = 8 - bits_e % 8
    if raise_bits_e != 8:
        num_e <<= raise_bits_e
        bits_e += raise_bits_e

    raise_bits = 8 - bits % 8
    if raise_bits != 8:
        num <<= raise_bits
        bits += raise_bits

    return ((num, bits), (num_e, bits_e))


def process_image():
    dy, dcb, dcr = read_frame()
    for y in range(int(im_h / 8)):
        for x in range(int(im_w / 8)):
            blk_y = get_block(dy, y, x, 8)
            blk_y = process_block(blk_y, qy)
            ser_y = zigzag_8(blk_y)
            (huf_y, enc_y) = huffman(ser_y[1:])

            fileout.write((ser_y[0] + 128).to_bytes(1, 'big'))
            fileout.write(enc_y[0].to_bytes(int(enc_y[1] / 8), 'big'))
            fileout.write(huf_y[0].to_bytes(int(huf_y[1] / 8), 'big'))

    for y in range(int(im_h / 16)):
        for x in range(int(im_w / 16)):
            blk_cb = get_block(dcb, y, x, 8)
            blk_cb = process_block(blk_cb, qc)
            ser_cb = zigzag_8(blk_y)
            (huf_cb, enc_cb) = huffman(ser_y[1:])

            fileout.write((ser_cb[0] + 128).to_bytes(1, 'big'))
            fileout.write(enc_cb[0].to_bytes(int(enc_cb[1] / 8), 'big'))
            fileout.write(huf_cb[0].to_bytes(int(huf_cb[1] / 8), 'big'))

    for y in range(int(im_h / 16)):
        for x in range(int(im_w / 16)):
            blk_cr = get_block(dcr, y, x, 8)
            blk_cr = process_block(blk_cr, qc)
            ser_cr = zigzag_8(blk_y)
            (huf_cr, enc_cr) = huffman(ser_y[1:])

            fileout.write((ser_cr[0] + 128).to_bytes(1, 'big'))
            fileout.write(enc_cr[0].to_bytes(int(enc_cr[1] / 8), 'big'))
            fileout.write(huf_cr[0].to_bytes(int(huf_cr[1] / 8), 'big'))


start = datetime.now()
f_start = 24 * 40
f_end = 24 * 41

tbar = Bar("Compressing images..", max=(f_end - f_start))

for x in range(f_end - f_start):
    process_image()
    tbar.next()

tbar.finish()

filein.close()
fileout.close()
print("Took ", datetime.now() - start)
