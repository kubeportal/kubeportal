FROM node:current-buster

# Install psycopg2 only in Docker image
# Putting it into requirements-prod.txt would not work
# for developers with ARM machines (e.g. new Macs)
RUN apt-get update && \
    apt-get install -y rustc python3 python3-pip vim sqlite3 postgresql-client npm && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir psycopg2 uwsgi

COPY requirements-prod.txt /tmp/

RUN pip3 install --no-cache-dir -r /tmp/requirements-prod.txt && \
    mkdir /code/ && \
    mkdir /data/

COPY . /code/

ENV KUBEPORTAL_STATIC_ROOT='/code/static-collected'
ENV KUBEPORTAL_STATICFILES_DIRS='/code/kubeportal/static'

# Go to folder with Vue.js sources, compile everything and
# then make the resulting dist-folder (see vue.config.js)
# the new frontend folder
# after that, let Django collect everything for static serving
RUN cd /code/kubeportal/static/frontend && \
    npm install && \
    npm run build && \
    cd .. && \
    rm -rf frontend && \
    mv frontend_dist frontend && \
    /usr/bin/python3 /code/manage.py collectstatic --noinput --configuration=Production

EXPOSE 8000

CMD ["/bin/sh", "/code/deployment/docker/docker-entry.sh"]

