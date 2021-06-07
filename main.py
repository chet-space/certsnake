#/bin/bash
import os
import boto3
import subprocess
from subprocess import PIPE
from pprint import pprint
import concurrent.futures
import configuration


def certsnake_aws():
    client = boto3.client(
        service_name='route53'
    )

    paginator = client.get_paginator('list_resource_record_sets')
    response_iterator = paginator.paginate(HostedZoneId=configuration.HostedZoneId)

    domain_list = []
    for key in response_iterator:
        recordsets = key['ResourceRecordSets']
        for record in recordsets:
            if record['Type'] == 'CNAME' or record['Type'] == 'A':
                domain_list.append(record)

    return domain_list


def certsnake_bot(domain):
    domain_name = (domain['Name'].strip('.'))
    config_file = "cli.ini"
    print(domain_name)

    config_parent = "config"
    logs_parent = "logs"
    work_parent = "work"

    config_dir = os.path.join(config_parent, domain_name)
    work_dir = os.path.join(work_parent, domain_name)
    logs_dir = os.path.join(logs_parent, domain_name)

    dirs = [config_dir, work_dir, logs_dir]

    for my_dir in dirs:
        if os.path.isdir(my_dir) is False:
            os.makedirs(my_dir)

    command = f"certbot --config-dir {config_dir}/ --logs-dir {logs_dir}/ --work-dir {work_dir}/ " \
              f"certonly --dns-route53 -d {domain_name} --agree-tos -n -c {config_file} " \
              f"--user-agent ''"

    comp_process = subprocess.run(args=['bash', '-c', command], stdout=PIPE, stderr=PIPE)
    pprint(comp_process.stderr)
    pprint(comp_process.stdout)


if __name__ == '__main__':
    domains = certsnake_aws()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(certsnake_bot, domain): domain for domain in domains}
