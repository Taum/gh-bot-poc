docker build -t gh-bot-poc .
docker run --env-file=.env gh-bot-poc
