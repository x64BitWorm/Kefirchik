FROM python:3.11-slim

WORKDIR /Application

COPY requirements.txt ./
RUN pip install -r requirements.txt --upgrade

COPY Backend ./

ENTRYPOINT ["python", "main.py"]
