from ip_reporting.aws_wrapper import set_route53_ip
from ip_reporting.ip_address_resolver import get_common_address


def main():
    ip_addr = get_common_address()
    set_route53_ip(ip_addr)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
