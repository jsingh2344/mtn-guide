#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements.txt
python manage.py collectstatic --no-input

if [[ "${IMPORT_DATA_DURING_BUILD:-false}" == "true" ]]; then
  python manage.py migrate --no-input
  python manage.py scrape_summitpost_wyoming
  python manage.py scrape_summitpost_peru
fi
