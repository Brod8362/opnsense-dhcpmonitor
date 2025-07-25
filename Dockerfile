FROM docker.io/python:3.13.5-bookworm
WORKDIR /app
COPY monitor.py /app/monitor.py
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "monitor.py"]