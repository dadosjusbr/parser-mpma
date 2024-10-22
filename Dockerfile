# set base image (host OS)
FROM python:3.8-slim-buster

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    libreoffice \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local directory to the working directory
COPY src/ .

# command to run on container start
CMD [ "python", "./main.py" ]