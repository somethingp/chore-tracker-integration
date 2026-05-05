ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python + dependencies
# gunicorn is more reliable than Flask dev server for production
RUN apk add --no-cache python3 py3-pip \
 && pip3 install --no-cache-dir flask==3.0.3 flask-cors==4.0.1 gunicorn==21.2.0 --break-system-packages

# Copy rootfs (service scripts + server)
COPY rootfs /

# Ensure all scripts are executable
RUN chmod +x /etc/services.d/chore-tracker/run \
 && chmod +x /etc/services.d/chore-tracker/finish \
 && chmod +x /usr/bin/chore_tracker.py
