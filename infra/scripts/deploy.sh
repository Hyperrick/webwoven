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
redirect_address=$(read_env WEBWOVEN_REDIRECT_ADDRESS)
analytics_address=$(read_env WEBWOVEN_ANALYTICS_ADDRESS)
analytics_website_id=$(read_env WEBWOVEN_ANALYTICS_WEBSITE_ID)
analytics_domain=$(read_env WEBWOVEN_ANALYTICS_DOMAIN)
session_secret=$(read_env WEBWOVEN_SESSION_SECRET)
edge_secret=$(read_env WEBWOVEN_EDGE_SECRET)
postgres_password=$(read_env POSTGRES_PASSWORD)
umami_database_password=$(read_env UMAMI_DATABASE_PASSWORD)
umami_app_secret=$(read_env UMAMI_APP_SECRET)
umami_admin_password=$(read_env UMAMI_ADMIN_PASSWORD)
graph_dir=$(read_env WEBWOVEN_GRAPH_DIR)

if [ "$environment" != "production" ]; then
  echo "WEBWOVEN_ENV must be production." >&2
  exit 1
fi
if [ "$cookie_secure" != "true" ]; then
  echo "WEBWOVEN_COOKIE_SECURE must be true." >&2
  exit 1
fi
for address in \
  "$origin" \
  "$api_origin" \
  "$site_address" \
  "$redirect_address" \
  "$analytics_address"; do
  case "$address" in
    https://*) ;;
    *)
      echo "Production origins and the site address must use HTTPS." >&2
      exit 1
      ;;
  esac
done
if [ "$site_address" = "$redirect_address" ] || [ "$site_address" = "$analytics_address" ]; then
  echo "The canonical site, redirect, and analytics addresses must be different." >&2
  exit 1
fi
case "$analytics_domain" in
  "" | *://* | */*)
    echo "WEBWOVEN_ANALYTICS_DOMAIN must be a hostname without a scheme or path." >&2
    exit 1
    ;;
esac

reject_placeholder WEBWOVEN_SESSION_SECRET "$session_secret" 32
reject_placeholder WEBWOVEN_EDGE_SECRET "$edge_secret" 32
reject_placeholder POSTGRES_PASSWORD "$postgres_password" 24
reject_placeholder WEBWOVEN_ANALYTICS_WEBSITE_ID "$analytics_website_id" 32
reject_placeholder UMAMI_DATABASE_PASSWORD "$umami_database_password" 24
reject_placeholder UMAMI_APP_SECRET "$umami_app_secret" 32
reject_placeholder UMAMI_ADMIN_PASSWORD "$umami_admin_password" 16
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
export WEBWOVEN_REDIRECT_ADDRESS="$redirect_address"
export WEBWOVEN_ANALYTICS_ADDRESS="$analytics_address"
export WEBWOVEN_ANALYTICS_WEBSITE_ID="$analytics_website_id"
export WEBWOVEN_ANALYTICS_DOMAIN="$analytics_domain"
export WEBWOVEN_SESSION_SECRET="$session_secret"
export WEBWOVEN_EDGE_SECRET="$edge_secret"
export POSTGRES_PASSWORD="$postgres_password"
export UMAMI_DATABASE_PASSWORD="$umami_database_password"
export UMAMI_APP_SECRET="$umami_app_secret"
export UMAMI_ADMIN_PASSWORD="$umami_admin_password"
export WEBWOVEN_GRAPH_DIR="$graph_dir"

sh infra/scripts/verify-graph.sh "$graph_dir"
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml pull --ignore-buildable
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml build api caddy
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml up -d analytics-db analytics
sh infra/scripts/bootstrap-analytics.sh
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml up -d --remove-orphans
docker compose --env-file .env -f docker-compose.yml -f docker-compose.production.yml ps
