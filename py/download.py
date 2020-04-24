import requests
from multiprocessing import Pool


def job(frame):
    name = "https://media.xiph.org/BBB/BBB-360-png/big_buck_bunny_{0:05d}.png".format(
        frame)
    r = requests.get(name)
    if(not r.ok):
        print("Failed to get {0}, {1}".format(name, r.status_code))
        return
    out_file = open("frames/{0:05d}.png".format(frame), "wb")
    out_file.write(r.content)
    out_file.close()


f_start = 24 * 40
f_end = 24 * 41


def main():
    pool = Pool()
    pool.map(job, range(f_start, f_end))


if __name__ == "__main__":
    main()
