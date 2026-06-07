FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gnuradio \
        python3-gnuradio \
        gr-osmosdr \
        rtl-sdr \
        soapysdr-tools \
        soapysdr-module-rtlsdr \
        soapysdr-module-hackrf \
        hackrf \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY receiver.py demod_service.py /app/

EXPOSE 8000

ENV DEMOD_HOST=0.0.0.0
ENV DEMOD_PORT=8000
ENV RTL_TCP_HOST=host.docker.internal
ENV RTL_TCP_PORT=1234

CMD ["python3", "/app/demod_service.py"]
