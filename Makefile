EXTENSION = rikai
DATA = sql/rikai--0.1.sql

PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)


docker:
	rm -rf dist
	python3 setup.py bdist_wheel
	docker build -t rikai-pg .
.PHONY: docker

run: docker
	docker run -v ${PWD}/tools/init.sql:/docker-entrypoint-initdb.d/0.sql \
		-e POSTGRES_HOST_AUTH_METHOD=trust \
		-p 5432:5432 rikai-pg
.PHONY: run

test:
	docker rm -f pg-test || true
	docker run -d -v ${PWD}/tools/init.sh:/docker-entrypoint-initdb.d/init.sh \
		-v ${PWD}/tests:/opt/tests/ \
		-e POSTGRES_HOST_AUTH_METHOD=trust \
		--name pg-test \
		rikai-pg
	sleep 5
	docker exec -t pg-test /bin/bash -c \
		"pg_prove -v -h localhost -U postgres /opt/tests/sql/*.sql"
	docker rm -f pg-test

