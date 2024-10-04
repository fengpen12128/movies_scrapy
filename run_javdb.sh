#!/bin/bash
cd /root/movies_scrapy
scrapy crawl javdb >> /root/movies_scrapy/javdb_$(date +\%Y\%m\%d).log 2>&1
