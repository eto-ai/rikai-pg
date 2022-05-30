FROM postgres:14

RUN apt-get update -y \
	&& apt-get install -y -qq git postgresql-plpython3-14 postgresql-server-dev-14 postgresql-14-pgtap make python3-pip \
	&& apt-get clean \
	&& pip install --no-cache-dir "rikai[pytorch,sklearn]>0.1" \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /build
COPY sql /build/sql
COPY Makefile rikai.control dist/*.whl /build/
RUN cd /build \
	&& make install \
	&& pip install --no-cache-dir /build/*.whl

RUN cd /tmp \
	&& git clone --branch v0.2.6 https://github.com/pgvector/pgvector.git \
	&& cd pgvector \
	&& make -j \
	&& make install
