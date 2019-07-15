FROM python:3.7.3-alpine
COPY . /app
WORKDIR /app
#RUN apt-get -y update && apt-get -y upgrade && apt-get install --no-install-recommends -y libsasl2-dev python-dev libldap2-dev libssl-dev && rm -rf /var/lib/apt/lists/*
RUN apk add --no-cache gcc
RUN pip3 install -r requirements.txt 
ENTRYPOINT ["python"]
CMD ["app.py"]
