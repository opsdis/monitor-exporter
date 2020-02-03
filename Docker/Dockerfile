FROM python:3

WORKDIR /app

COPY ./ ./

RUN pip install --upgrade pip && pip install -r requirements.txt && python setup.py sdist && pip install dist/monitor-exporter-0.2.1.tar.gz

CMD [ "python", "-m", "monitor_exporter", "-f", "config.yml" ]
