#!/usr/bin/env bash

set -e

declare -px > /app/cron.env

crontab /app/crontab
exec cron -f
