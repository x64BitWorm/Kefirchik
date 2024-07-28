FROM python:3.9-slim

WORKDIR /Application

COPY Backend ./

RUN pip install python-telegram-bot --upgrade
RUN pip install "python-telegram-bot[webhooks]"

ENTRYPOINT ["python", "main.py"]
