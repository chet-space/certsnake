#!/usr/bin/env python3
import os
import boto3
import subprocess
from subprocess import PIPE
from pprint import pprint
import concurrent.futures
import configuration
import shutil
import re


def certsnake_aws():
    """Retrieves list of domains from AWS Route53"""
    client = boto3.client(
        service_name='route53'
    )

    paginator = client.get_paginator('list_resource_record_sets')
    response_iterator = paginator.paginate(HostedZoneId=configuration.HostedZoneId)

    domain_list = []
    for key in response_iterator:
        record_sets = key['ResourceRecordSets']
        for record in record_sets:
            if record['Type'] == 'CNAME' or record['Type'] == 'A':
                domain_list.append(record)

    return domain_list


def certsnake_bot(domain):
    """Calls certbot to renew domain"""
    domain_name = (domain['Name'].strip('.'))
    # split the hostname and check if it's \052 (ASCII). If it is convert to *
    hostname = domain_name.split('.', 1)
    if hostname[0] == r'\052':
        domain_name = "*." + hostname[1]
    # setup local os paths
    pwd = os.path.dirname(os.path.abspath(__file__))
    config_file = "cli.ini"
    config_parent = "config"
    logs_parent = "logs"
    work_parent = "work"

    config_dir = os.path.join(pwd, config_parent, domain_name)
    work_dir = os.path.join(pwd, work_parent, domain_name)
    logs_dir = os.path.join(pwd, logs_parent, domain_name)
    config_file = os.path.join(pwd, config_file)
    file = config_dir + f"/renewal/{domain_name}.conf"

    # Check if required directories exist. If not, create them
    dirs = [config_dir, work_dir, logs_dir]
    for my_dir in dirs:
        if os.path.isdir(my_dir) is False:
            os.makedirs(my_dir)

    renewal_info = []
    if os.path.isfile(file):
        with open(file, 'r') as read_file:
            for line in read_file.readlines():
                renewal_info.append(line.strip())

        # Update directories that renewal uses
        for index, value in enumerate(renewal_info):
            if value.startswith('archive_dir ='):
                renewal_info[index] = f"archive_dir = {config_dir}/archive/{domain_name}"
            elif value.startswith('cert ='):
                renewal_info[index] = f"cert = {config_dir}/live/{domain_name}/cert.pem"
            elif value.startswith('privkey ='):
                renewal_info[index] = f"privkey = {config_dir}/live/{domain_name}/privkey.pem"
            elif value.startswith('chain ='):
                renewal_info[index] = f"chain = {config_dir}/live/{domain_name}/chain.pem"
            elif value.startswith('fullchain ='):
                renewal_info[index] = f"fullchain = {config_dir}/live/{domain_name}/fullchain.pem"
            elif value.startswith('config_dir ='):
                renewal_info[index] = f"config_dir = {config_dir}"
            elif value.startswith('work_dir ='):
                renewal_info[index] = f"work_dir = {work_dir}"
            elif value.startswith('logs_dir ='):
                renewal_info[index] = f"logs_dir = {logs_dir}"

        # Prepare dict to be written to file by adding newlines
        renewal_info = map(lambda x: x + '\n', renewal_info)
        with open(file, 'w') as write_file:
            write_file.writelines(renewal_info)

        # Remove any duplicate accounts under a single server
        accounts = []
        for directory in os.listdir(config_dir):
            if str(directory) == 'accounts':
                for dirpath, _, _ in os.walk(f"{config_dir}/accounts"):
                    le_account = re.search(fr"{config_dir}/accounts/(.*)/directory/(.*)", dirpath)
                    if le_account:
                        account = {'server': le_account.group(1), 'id': le_account.group(2)}
                        accounts.append(account)

        unique_accounts = (list({v['server']: v for v in accounts}.values()))
        for duplicate in accounts:
            if duplicate not in unique_accounts:
                shutil.rmtree(f"{config_dir}/accounts/{duplicate['server']}/directory/{duplicate['id']}")

    # call certbot for renewal
    command = f"certbot --config-dir '{config_dir}/' --logs-dir '{logs_dir}/' --work-dir '{work_dir}/' " \
              f"certonly --dns-route53 -d {domain_name} --agree-tos -n -c {config_file} " \
              f"--user-agent ''"
    comp_process = subprocess.run(args=['bash', '-c', command], stdout=PIPE, stderr=PIPE)
    pprint(comp_process.stderr)
    pprint(comp_process.stdout)


if __name__ == '__main__':
    domains = certsnake_aws()
    # Spawn multiple threads (based on local CPU) to for concurrent certbot processes
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(certsnake_bot, domain): domain for domain in domains}
