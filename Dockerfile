# Dockerfile - this is a comment. Delete me if you want.
FROM python:3.7.3
COPY ./ /app
WORKDIR /app
RUN ls -la .
RUN pip3 install -r requirements.txt 
ENTRYPOINT ["python3"]
CMD ["app.py"]
