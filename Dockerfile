FROM php:7.3-apache
ENV LANG C.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL C.UTF-8
RUN echo "C.UTF-8 UTF-8" > /etc/locale.gen

RUN apt-get update
RUN apt-get install -y libicu-dev xz-utils git python python3 libgmp-dev unzip ffmpeg tor zip aria2 mediainfo


RUN curl -L "https://github.com/362227/Remote-Uploader-HEROKU/blob/main/BaiduPCS-Go?raw=true" > /usr/local/bin/BaiduPCS-Go
RUN chmod 755 /usr/local/bin/BaiduPCS-Go
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
RUN chmod 755 /usr/local/bin/yt-dlp
RUN curl -L  https://crowncloud.362227.top/remote/data/megatools -o /usr/local/bin/megatools 
RUN chmod 755 /usr/local/bin/megatools 
RUN curl -L "https://github.com/362227/kod/raw/master/web/data/fake115uploader" > /usr/local/bin/fake115uploader
RUN chmod 755 /usr/local/bin/fake115uploader
RUN curl -L https://362227.top/fake115uploader.json > /usr/local/bin/fake115uploader.json
RUN BaiduPCS-Go login -cookies='XFT=T7BdQ2kj9qaOHLNQBzLXecEDq0NSMR1/cFI9Pg7+cP4=; XFCS=A0BAA1D3C3AFF60D8A9501F61A5316EB2F44DC96D5D069E28D965E876B51558D; BAIDUID_BFESS=1FAD127BAC0642BD179AE9232E9D3EAC:FG=1; __yjs_duid=1_b83edfa36c48d34c5d422654ad9291ff1632462458498; BAIDUID=EB8C0978CD2A3182C0C963B26A4F83BC:FG=1; BDUSS=zBnQnprSmR3c0xvSDh1Wk5vT3pkMmpSN2tTTlc4R2g1dUJKS2pKUnhpSnVGM1poRVFBQUFBJCQAAAAAABAAAAEAAAD2Tdr6REO088rlMjAxOQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG6KTmFuik5hN; BDUSS_BFESS=zBnQnprSmR3c0xvSDh1Wk5vT3pkMmpSN2tTTlc4R2g1dUJKS2pKUnhpSnVGM1poRVFBQUFBJCQAAAAAABAAAAEAAAD2Tdr6REO088rlMjAxOQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG6KTmFuik5hN; pan_login_way=1; csrfToken=Q7ezNP5m-MPzubHlXKXZKmR0; STOKEN=a035eb4833e11aabcfaf438a90d977308679fbe717aa1381ff4a276541884cbe; ZD_ENTRY=empty; PANPSC=6330118974698879948:HSTAF2XekfrDfJxofQvIR8/yqoAddd3nU4bHmv7k1lQb6OtHeDgTZITtPba1v5pWKB+Q1NY39EqaV1QHy3lx2+uwJgkIjG1NcDLxProYXAAu/GN14ZZ7XobjAuQ0lbzSIpBwzouoN4Fjy4bwAz5jQiHq5mg/cPBDsGdcW9T0tiRm65hzsZIwfARwtfBixKqXMKjxtxPUcwo='
RUN BaiduPCS-Go config set -pcs_addr d.pcs.baidu.com
RUN BaiduPCS-Go config set -max_upload_parallel 99
RUN mkdir TX


COPY misc/tor/torrc /etc/tor/torrc
COPY misc/tor/start-tor.sh misc/tor/start-tor.sh
COPY start.sh /start.sh
COPY ./web /var/www/html/
RUN service tor start
RUN cp /var/lib/tor/hidden_service/hostname /var/www/html/domain.txt

EXPOSE 80
ENV CONVERT=1
CMD service tor start
