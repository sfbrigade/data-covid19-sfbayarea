# This Docker image setup is designed primarily for development use. You *can*
# use it to run the scraper tools in a "production" capacity, but it's a lot
# heavier weight, with extra tools & dependencies, than you'll need.
FROM python:3.8-slim-buster

# Debian does not support a stable package for Firefox. Instead, it has
# "Firefox-ESR (Extended Support Release)", which is not very up-to-date, and
# does not seem to work too well with geckodriver. (It might be possible, but
# certainly needs some massaging I haven't figured out.)
# 
# Instead, use Debian's "unstable" source to get an up-to-date Firefox.
# We can also install Firefox by downloading the binary from Mozilla, but using
# APT helps make sure we have all the necessary dependencies.
# 
# More about Firefox on Debian: https://wiki.debian.org/Firefox
RUN sh -c 'echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" >> /etc/apt/sources.list'
RUN sh -c 'echo "APT::Default-Release "stable";" >> /etc/apt/apt.conf' 
RUN apt-get update && apt-get install -y -t unstable firefox
# Install other binary dependencies needed for our Python app. This is mainly
# about libxml2 & libxslt, which are required for Python lxml.
# NOTE: we have to install the unstable versions of these packages because
# Firefox *also* uses some of them, and it requires newer versions than are
# supported by Debian's stable source.
RUN apt-get update && apt-get install -y -t unstable \
    gcc g++ pkg-config libxml2-dev libxslt-dev

# Install Geckodriver manually because the webdrivermanager package we normally
# use to install it currently has issues on Linux.
RUN apt-get update && apt-get install -y curl
RUN mkdir /temp-install && \
    cd /temp-install && \
    curl --location 'https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz' > geckodriver.tar.gz && \
    tar -xzf geckodriver.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    cd .. && \
    rm -rf temp-install

# The app source will be installed in /app, so make that the working directory.
WORKDIR /app

# Copy our dependency files and install from them separate from the rest of the
# app source so the can be cached more aggressively than the rest of the code.
ADD requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
ADD requirements-dev.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements-dev.txt

# Copy the rest of the source.
ADD . /app

# Since this is designed for development, launch with bash by default.
# NOTE: You can always launch the container directly into the scraper instead:
#     docker run python3 scraper_data.py
CMD ["/bin/bash"]
