#!/usr/bin/env bash
docker build -t data-covid19-sfbayarea .
docker run -it data-covid19-sfbayarea $@
