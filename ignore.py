from ipaddress import ip_address, ip_network, summarize_address_range, IPv4Address
from hilbertcurve.hilbertcurve import HilbertCurve
from PIL import Image, ImageDraw


class IgnoreStore:
    def __init__(self, file_path) -> None:
        self.file_path = file_path
        self.ignored_ips = []
        self.ignored_networks = []
        self.load_ignore_range()
        self.ignored_ips = set(self.ignored_ips)

    def load_ignore_range(self):
        with open(self.file_path) as file:
            for line in file:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                if "-" in line:
                    ip_start, ip_end = line.split("-")
                    ip_start = ip_address(ip_start)
                    ip_end = ip_address(ip_end)
                    self.ignored_networks.extend(
                        summarize_address_range(ip_start, ip_end)
                    )
                elif "/" not in line:
                    self.ignored_ips.append(ip_address(line))
                else:
                    self.ignored_networks.append(ip_network(line))

    def annotate_image(self, img: Image, hilbert: HilbertCurve, color=128):
        for ip in self.ignored_ips:
            point = hilbert.point_from_distance(ip._ip)
            img.putpixel(point, color)

        draw = ImageDraw.Draw(img)
        for network in self.ignored_networks:
            size = int(network.num_addresses**0.5 / 2)
            ip_mid = network[int(network.num_addresses / 2)]
            x_mid, y_mid = hilbert.point_from_distance(ip_mid._ip)
            draw.rectangle(
                [x_mid - size, y_mid - size, x_mid + size, y_mid + size], fill=color
            )

    def __contains__(self, ip: IPv4Address):
        for network in self.ignored_networks:
            if ip in network:
                return True

        return ip in self.ignored_ips

    def __iter__(self):
        for ip in self.ignored_ips:
            yield ip

        for network in self.ignored_networks:
            for ip in network:
                yield ip


if __name__ == "__main__":
    ignore = IgnoreStore("data/ignores.txt")
    hc = HilbertCurve(16, 2)
    img = Image.new("1", (2**16, 2**16))
    ignore.annotate_image(img, hc, color=1)
    img.save("out/fast_ignore.png")
