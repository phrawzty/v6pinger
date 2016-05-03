# v6pinger
Ping a series of IPv6 targets based on some criteria, and report on the results.

# Why?
So I have a bunch of hosts at a given third-party data centre that lose their IPv6 connectivity randomly.  The problem is upstream (ugh) and the solution is "restart networking" (ugggh).  I needed a way to test IPv6 connectivty with some flexibility - this little script scratches that particular itch.

# How?
There is an excellent IPv6 in-browser test suite called [Falling Sky](https://github.com/falling-sky) that powers http://test-ipv6.com, the source of which contains a *list* of IPv6 targets which can be pinged along with some related meta-data.

v6pinger will attempt to obtain that *list*, parse it according to some user-configurable options, and produce a series of hosts to test against.

# Config
There must be a file called `config.yaml` in the same directory as `v6pinger.py`. This file contains a number of configuration options, some of which are more likely to be toyed with than others - notably:

## `prefers`
The *list* contains meta-data for each host that can be used to help specify which hosts should appear in the test series. For example, to ensure that any hosts provided by `vr.org`, or with a `loc` field of `global` or `FR` are included :
```yaml
prefers:
    provider:
        - vr.org
    loc:
        - global
        - FR
```

## `min_test`
The minimum number of targets to test. Note that v6pinger will abort if this number of targets cannot be obtained for some reason.

## `max_test`
The maximum number of targets to test.  Note that v6pinger will fill the test series with randomly-selected targets if the `prefers` criteria doesn't produce enough targets. 

## `ratio`
A multiplier to determine how many successful targets are required in order to declare victory.  A multiplier of `0.5`, for example, would mean that half of the targets must be pingable.

## `sites_age`
The maximum age (in seconds) of the cached *list* after which a fresh copy will be otained.

# Usage
```bash
$ ./v6pinger.py
```

In my express case, I put it in a wrapper that's more or less like this :
```bash
#!/usr/bin/env bash

cd /opt/v6pinger/
. ./.venv/bin/activate
./v6pinger.py
if [[ $? -eq 1 ]]; then
    echo "[ERROR] Something went wrong!" 1>&2
elif [[ $? -gt 1 ]]; then
    echo "[ERROR] restarting dibbler" 1>&2
    /usr/sbin/service dibbler-client restart
fi
deactivate
```

With a cron job to capture `STDERR` as necessary :
```bash
*/5 * * * * root /opt/v6pinger/cron_wrapper.sh > /dev/null | logger -i -t v6pinger
```
