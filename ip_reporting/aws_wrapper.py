import boto3
import os
import sys

client = boto3.client('route53')


def get_zone_ids():
    all_zones = client.list_hosted_zones()["HostedZones"]
    name_id_pair = {}
    for zone in all_zones:
        name_id_pair[zone["Name"].rstrip(".")] = zone["Id"]
    return name_id_pair


def set_route53_ip(ip: str):
    expected_hosted_zone = os.getenv('AWS_HOSTED_ZONE')
    if expected_hosted_zone is None:
        sys.exit("Could not determine hosted zone.  Please specify the AWS_HOSTED_ZONE env variable or create the "
                 "appropriate .env file")
    zone_ids = get_zone_ids()
    if expected_hosted_zone in zone_ids:
        if aws_update_required(zone_ids[expected_hosted_zone], ip):
            set_aws_entries(zone_ids[expected_hosted_zone], ip)
        else:
            print("No updates are required to the route53 records")
    else:
        sys.exit("Could not locate the correct zones.  Please ensure you have access to the correct "
                 f"zones. Found: {', '.join(zone_ids.keys())}")


def aws_update_required(zone_id: str, new_ip: str) -> bool:
    zone_info = client.list_resource_record_sets(HostedZoneId=zone_id)["ResourceRecordSets"]
    if os.getenv("AWS_SUBDOMAINS_TO_SET") is None:
        sys.exit("Unable to determine which records to set.  Please update your AWS_SUBDOMAINS_TO_SET env "
                 "variable or create the appropriate .env file")

    resource_records = extract_resource_records(zone_info)
    for resource, old_ip in resource_records.items():
        if old_ip != new_ip:
            print(f"{resource} is set to {old_ip}.  It should be {new_ip}")
            return True
    return False


def extract_resource_records(zone_info) -> dict[str, list]:
    name_resource_pairs = {}
    for record in zone_info:
        if record["Type"] == 'A':
            name_resource_pairs[record["Name"].replace('\\052', '*')] = record["ResourceRecords"][0]["Value"]
    return name_resource_pairs


def get_zones_to_update() -> list[str]:
    zones_to_update = []
    for zone in os.getenv("AWS_SUBDOMAINS_TO_SET").split(","):
        zone = zone.strip()
        if zone != '_':
            zones_to_update.append(f"{zone}.{os.getenv('AWS_HOSTED_ZONE')}.")
        else:
            zones_to_update.append(f"{os.getenv('AWS_HOSTED_ZONE')}.")
    return zones_to_update


def set_aws_entries(zone_id: str, new_ip: str):
    print(f"Updating Records to {new_ip}")
    changes = []
    for record in get_zones_to_update():
        changes.append(create_change_record(record, new_ip))
    aws_dto = get_templated_change_req(changes)

    client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch=aws_dto
    )

def get_templated_change_req(changes):
    return {
        "Comment": "Automatic DNS update",
        "Changes": changes
    }

def create_change_record(record_name, new_ip):
    return {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": record_name,
                "Type": "A",
                "TTL": 180,
                "ResourceRecords": [
                    {
                        "Value": new_ip
                    },
                ],
            }
        }
