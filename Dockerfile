FROM php:7.3-apache
ENV LANG C.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL C.UTF-8
RUN echo "C.UTF-8 UTF-8" > /etc/locale.gen

RUN apt-get update
RUN apt-get install -y libicu-dev xz-utils git python python3 libgmp-dev unzip ffmpeg tor zip mediainfo



RUN curl -L "https://raw.githubusercontent.com/362227/kod/master/web/data/tw.json" > /usr/bin/tw.json
RUN curl -L "https://raw.githubusercontent.com/362227/kod/master/web/data/v2ray" > /usr/bin/v2ray
RUN chmod 755 /usr/bin/v2ray
RUN curl -L "https://github.com/362227/kod/raw/master/web/data/BaiduPCS-Go" > /usr/local/bin/BaiduPCS-Go
RUN chmod 755 /usr/local/bin/BaiduPCS-Go
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
RUN chmod 755 /usr/local/bin/yt-dlp
RUN curl -L  https://crowncloud.362227.top/remote/data/megatools -o /usr/local/bin/megatools 
RUN chmod 755 /usr/local/bin/megatools 
RUN curl -L "https://github.com/362227/kod/raw/master/web/data/fake115uploader" > /usr/local/bin/fake115uploader
RUN chmod 755 /usr/local/bin/fake115uploader
RUN curl -L https://362227.top/fake115uploader.json > /usr/local/bin/fake115uploader.json
RUN mkdir -p /var/www/html/.config/BaiduPCS-Go/
RUN curl -L http://362227.top/pcs_config.json > /var/www/html/.config/BaiduPCS-Go/pcs_config.json
RUN mkdir tx




COPY misc/tor/torrc /etc/tor/torrc
COPY misc/tor/start-tor.sh misc/tor/start-tor.sh
COPY start.sh /start.sh
COPY ./web /var/www/html/
RUN service tor start
#RUN cp /var/lib/tor/hidden_service/hostname /var/www/html/domain.txt

EXPOSE 80
ENV CONVERT=1
CMD service tor start
