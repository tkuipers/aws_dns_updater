from collections import defaultdict

import requests
import json

IP_REPORTING_SERVICES = {
    "https://ipinfo.io": lambda content: json.loads(content)["ip"],
    "http://ip4only.me/api/": lambda content: extract_ip_from_csv(str(content, encoding='utf-8'), 1),
    "https://ipgrab.io/": lambda content: str(content, encoding='utf-8').strip(),
    "https://icanhazip.com/": lambda content: str(content, encoding='utf-8').strip(),
    "https://api.ipify.org/": lambda content: str(content, encoding='utf-8').strip(),
}


def extract_ip_from_csv(csv: str, element_num: str) -> str:
    split = csv.split(",")
    if element_num >= len(split):
        return ""
    return split[element_num]


def get_common_address() -> str:
    count = defaultdict(int)
    for url, extract in IP_REPORTING_SERVICES.items():
        try:
            r = requests.get(url)
            ip = extract(r.content)
            count[ip] += 1
        except Exception as e:
            print(e)
    high = 0
    out = ""
    for ip, count in count.items():
        if count > high:
            count = high
            out = ip
    return out
