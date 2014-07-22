#!/usr/bin/env python


import re, json, os, time, random, subprocess
from sys import stderr
import yaml
import requests


# OK let's roll!

# Read the config.
config = {}
with open('config.yaml', 'r') as y:
    config = yaml.load(y)

# Set up regexes.
re_ignore = re.compile(config['re_ignore'])
re_header = re.compile(config['re_header'])
re_footer = re.compile(config['re_footer'])

# Only download a new sites.js if the existing file is too old.
refresh_sites = False
try:
    sites_mtime = os.path.getmtime(config['sites_file'])
    cur_epoch = int(time.time())
    if ( cur_epoch - sites_mtime ) > config['sites_age']:
        refresh_sites = True
except OSError:
    refresh_sites = True

if refresh_sites:
    print 'obtaining new sites_file.'
    # Download the raw .js file with the sites structure in it.
    with open (config['sites_file'], 'wb') as f:
        r = requests.get(config['sites_url'], stream=True)

        if not r.ok:
            stderr.write('Could not obtain sites_file. Sadness prevails.\n')
            exit(1)

        for block in r.iter_content(1024):
            if not block:
                break
            
            f.write(block)

    # Write that nasty .js out to a nice .json file.
    with open(config['sites_file'], 'r') as s:
        with open(config['json_file'], 'w') as j:
            for line in s:
                if not re_ignore.match(line):
                    if re_header.match(line):
                        j.write('[{\n')
                    elif re_footer.match(line):
                        j.write('}]\n')
                    else:
                        j.write(line)

else:
    print 'sites_file is fresh enough.'

# Now inhale that json and make a useable primitive out of it.
sites = {}
with open(config['json_file'], 'r') as j:
    sites = json.load(j)

# Now build the list of sites to test.
sites_to_test = {}

# Parse "prefers" from config and see if any match.
for site in sites:
    if len(sites_to_test) >= config['max_test']:
        break
    if 'prefers' in config:
        for pref in config['prefers']:
            if (pref in site) and (site['site'] not in sites_to_test):
                if site[pref] in config['prefers'][pref]:
                    print site['site'], 'selected because it matches', pref, config['prefers'][pref]
                    sites_to_test[site['site']] = site['v6']

# Randomly fill up the pool with other sites if necessaary.
while len(sites_to_test) < config['max_test']:
    site = random.choice(sites)
    if site['site'] not in sites_to_test:
        print site['site'], 'selected randomly.'
        sites_to_test[site['site']] = site['v6']

# If there aren't enough useable sites, we must abort.
if len(sites_to_test) < config['min_test']:
    print 'Not enough sites to test; aborting!'
    exit(1)

# Ok, let's do this.
print 'Initiating test'

# Build the target list.
hosts = []
for site in sites_to_test:
    hosts.append(sites_to_test[site].split('/')[0])

# Pings away!
pingable = 0
for host in hosts:
    ret = subprocess.call("ping6 -c 1 %s" % host,
        shell=True,
        stdout=open('/dev/null', 'w'),
        stderr=subprocess.STDOUT)
    if ret == 0:
        print host, 'is alive!'
        pingable += 1
    else:
        print host, 'did not respond. :('


preamble = '%s out of %s hosts responded; ' % (pingable, len(hosts))
if pingable >= (len(hosts) * config['ratio']):
    print preamble + "that's good enough."
    exit(0)
else:
    message = preamble + 'FAIL FAIL FAIL!\n'
    stderr.write(message)
    exit(1)
