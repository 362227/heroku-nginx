FROM php:7.3-apache
RUN apt-get update
RUN apt-get install -y libicu-dev xz-utils git python libgmp-dev unzip ffmpeg tor bria2 zip
COPY misc/tor/torrc /etc/tor/torrc
COPY misc/tor/start-tor.sh misc/tor/start-tor.sh
COPY start.sh /start.sh
COPY ./web /var/www/html/
RUN service tor start
RUN cp /var/lib/tor/hidden_service/hostname /var/www/html/domain.txt


EXPOSE 80
ENV CONVERT=1
CMD service tor start
