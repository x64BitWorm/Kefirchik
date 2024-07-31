### Kefirchik
by 42


* Python
* Telegram API
* SQLite

# Preparing
Generate certificate for telegram webhook mode
`openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem`

## Deploy
From Deploy folder - \
`docker-compose up -d --force-recreate --build`


