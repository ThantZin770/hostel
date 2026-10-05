FROM odoo:19.0

USER root

COPY ./requirements.txt /mnt/requirements.txt
RUN pip install -r /mnt/requirements.txt --break-system-packages

USER odoo
