FROM python:3.6

EXPOSE 9631

COPY . /monitor-exporter

RUN mkdir -p /monitor-exporter/config

WORKDIR /monitor-exporter

RUN mv config.yml /monitor-exporter/config

RUN pip3 install -r requirements.txt

RUN python setup.py sdist

ENTRYPOINT [ "python" ]

CMD ["-m", "monitor_exporter", "-f",  "/monitor-exporter/config/config.yml" ]
