#!/bin/bash

psql <<EOF
CREATE EXTENSION plpython3u;
CREATE EXTENSION rikai;

INSERT INTO ml.models (name, flavor, model_type)
VALUES ('ssd', 'pytorch', 'ssd');

INSERT INTO ml.models (name, flavor, model_type)
VALUES ('embedding', 'pytorch', 'features');

-- Test data
-- See images in rikai/tests/conftest.py
CREATE EXTENSION IF NOT EXISTS pgtap;  -- For unit test

CREATE TABLE images (
image_id SERIAL PRIMARY KEY,
image image,
embedding real[]
);
INSERT INTO images (image)
VALUES
(Row('http://farm2.staticflickr.com/1129/4726871278_4dd241a03a_z.jpg')),
(Row('http://farm4.staticflickr.com/3726/9457732891_87c6512b62_z.jpg'));

UPDATE images SET embedding = ml.embedding(image);
EOF


