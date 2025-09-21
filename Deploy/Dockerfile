FROM python:3.11-slim

WORKDIR /Application

COPY Backend ./

RUN pip install python-telegram-bot "python-telegram-bot[webhooks]" SQLAlchemy --upgrade

ENTRYPOINT ["python", "main.py"]
