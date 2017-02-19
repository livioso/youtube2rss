FROM python:3.4
LABEL maintainer="Livio Bieri <contact@livio.li>"

ADD requirements.txt .
RUN pip3 install -r ./requirements.txt

RUN mkdir -p /usr/app /usr/app/out
COPY . /usr/app
WORKDIR /usr/app

# run youtube2rss for each given config file:
# mount volume with configs to /usr/app/configs
CMD cd out; for config in ../configs/*.json; do python3 ../youtube2rss/main.py $config; done;
