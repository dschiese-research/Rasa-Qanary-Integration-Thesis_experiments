FROM python:3.8-slim

RUN python3.8 -m pip install rasa

WORKDIR /app
COPY . .

RUN rasa train

#Setting user as someone not-root
USER 1001

ENTRYPOINT ["rasa"]
VOLUME /app
VOLUME /app/data
VOLUME /app/models

CMD ["run", "--enable-api", "--cors", "*", "--port", "5005", "--endpoints", "endpoints.yml"]
