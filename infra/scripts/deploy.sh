#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Create a production .env before deploying." >&2
  exit 1
fi

read_env() {
  sed -n "s/^$1=//p" .env | tail -n 1 | tr -d '\r'
}

reject_placeholder() {
  name=$1
  value=$2
  minimum=$3
  normalized=$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')
  case "$normalized" in
    "" | development-* | replace-with-*)
      echo "$name must be a unique production value." >&2
      exit 1
      ;;
  esac
  if [ "${#value}" -lt "$minimum" ]; then
    echo "$name must contain at least $minimum characters." >&2
    exit 1
  fi
  unique_characters=$(printf '%s' "$value" | fold -w 1 | LC_ALL=C sort -u | wc -l | tr -d ' ')
  if [ "$unique_characters" -lt 8 ]; then
    echo "$name must not be a low-entropy repeated value." >&2
    exit 1
  fi
}

environment=$(read_env WEBWOVEN_ENV)
cookie_secure=$(read_env WEBWOVEN_COOKIE_SECURE)
origin=$(read_env WEBWOVEN_ORIGIN)
api_origin=$(read_env WEBWOVEN_API_ORIGIN)
site_address=$(read_env WEBWOVEN_SITE_ADDRESS)
session_secret=$(read_env WEBWOVEN_SESSION_SECRET)
edge_secret=$(read_env WEBWOVEN_EDGE_SECRET)
postgres_password=$(read_env POSTGRES_PASSWORD)
graph_dir=$(read_env WEBWOVEN_GRAPH_DIR)

if [ "$environment" != "production" ]; then
  echo "WEBWOVEN_ENV must be production." >&2
  exit 1
fi
if [ "$cookie_secure" != "true" ]; then
  echo "WEBWOVEN_COOKIE_SECURE must be true." >&2
  exit 1
fi
for address in "$origin" "$api_origin" "$site_address"; do
  case "$address" in
    https://*) ;;
    *)
      echo "Production origins and the site address must use HTTPS." >&2
      exit 1
      ;;
  esac
done

reject_placeholder WEBWOVEN_SESSION_SECRET "$session_secret" 32
reject_placeholder WEBWOVEN_EDGE_SECRET "$edge_secret" 32
reject_placeholder POSTGRES_PASSWORD "$postgres_password" 24
if [ "$session_secret" = "$edge_secret" ]; then
  echo "Session and edge secrets must be different." >&2
  exit 1
fi
if [ -z "$graph_dir" ] || [ ! -d "$graph_dir" ]; then
  echo "WEBWOVEN_GRAPH_DIR must point to a verified graph bundle directory." >&2
  exit 1
fi

export WEBWOVEN_ENV="$environment"
export WEBWOVEN_COOKIE_SECURE="$cookie_secure"
export WEBWOVEN_ORIGIN="$origin"
export WEBWOVEN_API_ORIGIN="$api_origin"
export WEBWOVEN_SITE_ADDRESS="$site_address"
export WEBWOVEN_SESSION_SECRET="$session_secret"
export WEBWOVEN_EDGE_SECRET="$edge_secret"
export POSTGRES_PASSWORD="$postgres_password"
export WEBWOVEN_GRAPH_DIR="$graph_dir"

sh infra/scripts/verify-graph.sh "$graph_dir"
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml pull --ignore-buildable
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml build api caddy
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml up -d --remove-orphans
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml ps
