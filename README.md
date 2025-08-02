### Kefirchik
Most honest division of expenses in telegram groups
by 42

* Python
* Telegram API
* SQLite

Running bot [available](https://t.me/kefirchik42_bot) in telegram

# Preparing
Generate certificate for telegram webhook mode
`openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem`

## Deploy locally
Set token variable -
`$env:TG_TOKEN='...:...'`

Run -
```console
python3 main.py
```

## Deploy from docker locally
Contents of '/var/lib/kepirchik/.env' -
```console
TG_TOKEN=...:...
MODE=grisha
DB_PATH=/var/lib/kepirchik/kefirchik.db
```

Run -
```console
docker-compose up --env-file '/var/lib/kepirchik/.env' -d --force-recreate --build
```

## Deploy from docker on server
Contents of '/var/lib/kepirchik/.env' -
```console
TG_TOKEN=...:...
MODE=release
```

Run -
```console
docker-compose up --env-file '/var/lib/kepirchik/.env' -d --force-recreate --build
```

# Run/add tests
Run - `python3 tests_runner.py` \
Add new tests to `tests/main_flow_test.py` or another `tests/*_test.py` file

# More about implementation
[Scheme](./Assets/DEV.md)
