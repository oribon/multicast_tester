FROM python:3.7-alpine
RUN adduser -D dod
WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt
USER dod
CMD [ "python","-u", "./sender.py" ]