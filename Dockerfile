FROM python:3.7.3-alpine
COPY . /app
WORKDIR /app
RUN apk add --no-cache gcc linux-headers libc-dev musl-dev openldap-dev
RUN pip3 install -r requirements.txt 
ENTRYPOINT ["python"]
CMD ["app.py"]