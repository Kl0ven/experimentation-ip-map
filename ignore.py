from ipaddress import ip_address, ip_network, summarize_address_range, IPv4Address


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
    print(ignore)
