# Proof of Concept

This is a proof of concept for a Docker image that will load cards from a remote source and push them to a Github repository.

The `loader` directory would contain a Python script to load cards from the API or any other source.

The `scripts` directory has a script to run within the Docker image, this script will:
- Checkout a Github repository in a temporary directory
- Execute the Python `loader` script to load cards from a remote source
- Create a commit with the new files added to the repository
- Push the commit to a new branch
- Create a Pull Request

# How to run

## Create .env file and get a github token

Copy from .env.example and set your github token.

Get a token by following the instructions [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).

The token needs permissions:
- Contents: Read and Write (to create a branch and push to it)
- Pull-requests: Read and Write (to create a Pull Request)

## Build image

```
docker build -t gh-bot-poc .
```

## Run image with .env file

```
docker run --env-file=.env gh-bot-poc
```

