FROM python:3.7-alpine
RUN adduser -D dod
WORKDIR /usr/src/app
COPY . .
USER dod
CMD [ "python","-u", "./reciever.py" ]