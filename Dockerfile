FROM quay.io/astronomer/astro-runtime:10.4.0

USER root
RUN apt-get update && \
    apt-get install -y default-jre-headless && \
    apt-get clean

USER astro