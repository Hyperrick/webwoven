#!/usr/bin/env sh
set -eu

server_type=${WEBWOVEN_SERVER_TYPE:-cax21}
location=${WEBWOVEN_SERVER_LOCATION:-nbg1}
name=${WEBWOVEN_SERVER_NAME:-webwoven-build-week}

if ! command -v hcloud >/dev/null 2>&1; then
  echo "Install the Hetzner Cloud CLI before provisioning." >&2
  exit 1
fi

if [ -z "${HCLOUD_TOKEN:-}" ]; then
  echo "Set HCLOUD_TOKEN locally; never place it in the repository." >&2
  exit 1
fi

if [ "${CONFIRM_BILLABLE_SERVER:-}" != "$server_type" ]; then
  echo "Review the current Hetzner price, then set CONFIRM_BILLABLE_SERVER=$server_type." >&2
  exit 1
fi

hcloud server create \
  --name "$name" \
  --type "$server_type" \
  --location "$location" \
  --image ubuntu-24.04 \
  --user-data-from-file infra/cloud-init.yml
