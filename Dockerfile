# Build from python 2.7.12
# python 3 is better but laziness just happens to be my friend
FROM python:2.7.12

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

ENV  C_FORCE_ROOT=1

CMD ["/bin/sh", "./run.sh"]