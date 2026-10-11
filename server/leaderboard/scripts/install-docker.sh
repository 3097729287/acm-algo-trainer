#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then
  printf 'Run this installer with sudo.\n' >&2
  exit 1
fi
if command -v docker >/dev/null 2>&1; then
  docker version
  docker compose version
  exit 0
fi
. /etc/os-release
case "$ID:$VERSION_ID" in
  ubuntu:22.04|ubuntu:24.04|ubuntu:26.04|debian:12|debian:13) ;;
  *) printf 'Inspect this OS before installation: %s %s\n' "$ID" "$VERSION_ID" >&2; exit 1 ;;
esac
for package in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    printf 'Existing container package requires inspection: %s\n' "$package" >&2
    exit 1
  fi
done
if [ -e /etc/apt/sources.list.d/docker.sources ] || [ -e /etc/apt/sources.list.d/docker.list ]; then
  printf 'An existing Docker apt source requires inspection.\n' >&2
  exit 1
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl python3
install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/$ID
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
# Avoid Docker's default 172.17.0.0/16 bridge overlapping the host/VPC.
# Configure only a fresh installation, before the package starts the daemon.
if [ -e /etc/docker/daemon.json ]; then
  printf 'Existing daemon.json requires inspection before Docker installation.\n' >&2
  exit 1
fi
install -m 0755 -d /etc/docker
python3 - <<'PYNET'
import ipaddress
import json
import os
import subprocess
routes = json.loads(subprocess.check_output(['ip', '-j', '-4', 'route', 'show', 'table', 'all']))
addresses = json.loads(subprocess.check_output(['ip', '-j', '-4', 'addr', 'show']))
used = [ipaddress.ip_network(route['dst'], strict=False) for route in routes
        if route.get('dst') and route['dst'] != 'default']
used += [ipaddress.ip_network(info['local'] + '/' + str(info['prefixlen']), strict=False)
         for link in addresses for info in link.get('addr_info', []) if info.get('family') == 'inet']
for bridge, pool in [('10.201.0.1/24', '10.202.0.0/16'), ('10.241.0.1/24', '10.242.0.0/16'),
                     ('192.168.160.1/24', '192.168.164.0/22')]:
    selected = [ipaddress.ip_network(bridge, strict=False), ipaddress.ip_network(pool)]
    if any(candidate.overlaps(existing) for candidate in selected for existing in used):
        continue
    descriptor = os.open('/etc/docker/daemon.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, 'w') as output:
        json.dump({'bip': bridge, 'default-address-pools': [{'base': pool, 'size': 24}]}, output)
        output.write('\n')
    print('Configured Docker networks:', bridge, pool)
    break
else:
    raise SystemExit('No non-overlapping Docker address range found; inspect host routing.')
PYNET
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker version
docker compose version
docker run --rm hello-world
