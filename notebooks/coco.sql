-- DDL for Coco dataset example

-- VERSION 1

-- Main asset table
DROP TABLE IF EXISTS coco CASCADE;
CREATE TABLE coco (
                      image_id INTEGER PRIMARY KEY,
                      image IMAGE,
                      file_name CHAR(16),
                      height INTEGER,
                      width INTEGER,
                      split VARCHAR(5)
);

-- Exploded annotations
DROP TABLE IF EXISTS coco_gt CASCADE;
CREATE TABLE coco_gt (
                         id SERIAL PRIMARY KEY,
                         image_id INTEGER,
                         label varchar(100),
                         box BOX,
                         supercategory varchar(100),
                         CONSTRAINT fk_image_id
                             FOREIGN KEY(image_id)
                                 REFERENCES coco(image_id)
);

-- VERSION 2

-- Everything in one table with annotations as jsonb column
DROP TABLE IF EXISTS coco_det CASCADE;
CREATE TABLE coco_det (
                          image_id INTEGER PRIMARY KEY,
                          image IMAGE,
                          file_name CHAR(16),
                          height INTEGER,
                          width INTEGER,
                          split VARCHAR(5),
                          annotations JSONB
);
