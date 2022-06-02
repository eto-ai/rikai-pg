FROM postgres:14

RUN apt-get update -y \
	&& apt-get install -y -qq git postgresql-plpython3-14 postgresql-server-dev-14 postgresql-14-pgtap make python3-pip \
	&& apt-get clean \
	&& pip install --no-cache-dir "git+https://github.com/eddyxu/rikai.git@lei/fs_fixes#subdirectory=python&egg=rikai[pytorch,sklearn]>0.1" \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /build
COPY sql /build/sql
COPY Makefile rikai.control dist/*.whl /build/
RUN cd /build \
	&& make install \
	&& pip install --no-cache-dir /build/*.whl \
	&& apt-get remove -y -qq git make python3-pip postgresql-server-dev-14 \
	&& apt-get autoclean -y -qq \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /build

