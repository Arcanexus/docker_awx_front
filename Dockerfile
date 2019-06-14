# Dockerfile - this is a comment. Delete me if you want.
FROM python:2.7
COPY . /app
WORKDIR /app
ENV http_proxy http://10.20.102.6:3128
ENV https_proxy http://10.20.102.6:3128
ENV HTTP_PROXY http://10.20.102.6:3128
ENV HTTPS_PROXY http://10.20.102.6:3128
RUN pip install -r requirements.txt 
ENTRYPOINT ["python"]
CMD ["app.py"]
