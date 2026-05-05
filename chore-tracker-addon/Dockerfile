ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python + pip deps
RUN apk add --no-cache python3 py3-pip \
 && pip3 install --no-cache-dir flask==3.0.3 flask-cors==4.0.1

# Copy the API server
COPY rootfs /

RUN chmod +x /usr/bin/chore-tracker

CMD ["/usr/bin/chore-tracker"]
