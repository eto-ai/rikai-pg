-- Create Schema to contain all Rikai functionality
CREATE SCHEMA IF NOT EXISTS ml;

-- Semantic Types
CREATE TYPE image AS (uri TEXT);

CREATE TYPE detection AS (label TEXT, label_id int, box box, score real);

-- rikai.types.Mask
CREATE TYPE mask_type AS ENUM ('polygon', 'rle', 'coco_rle');

CREATE TYPE mask AS (
    type mask_type,
    rle INT[],
    polygons polygon[],
    width INT,
    height INT
);

-- Tables for ML metadata
CREATE TABLE ml.models (
	name VARCHAR(128) NOT NULL PRIMARY KEY,
	flavor VARCHAR(128) NOT NULL,
	model_type VARCHAR(128) NOT NULL,
	uri VARCHAR(1024),
	options JSONB DEFAULT '{}'::json
);
CREATE INDEX IF NOT EXISTS model_flavor_idx
ON ml.models (flavor, model_type);

-- Functions
CREATE OR REPLACE FUNCTION ml.version()
    RETURNS table (package varchar, version varchar)
AS $$
import sys
python_version = sys.version.splitlines()[0];
python_path = sys.path
rikai_version = ""
torch_version = ""
try:
    import rikai
    rikai_version = rikai.__version__.version
except ImportError as exc:
    plpy.error("Could not import Rikai", exc)
try:
    import torch
    torch_version = torch.version.__version__
except ImportError as exc:
    plpy.error("Could not import torch", exc)
return [
    ["python", python_version],
    ["rikai", rikai_version],
    ["torch", torch_version]
]
$$ LANGUAGE plpython3u;


CREATE FUNCTION ml.is_cuda_available()
    RETURNS BOOL
AS $$
import torch
return torch.cuda.is_available()
$$ LANGUAGE plpython3u;


CREATE FUNCTION ml.cuda_info()
    RETURNS JSON
AS $$
import json
import torch
def props(device_no):
    p = torch.cuda.get_device_properties(device_no)
    return {
        'name': p.name,
        'total_memory': p.total_memory,
        'processor_count': p.multi_processor_count
    }
return json.dumps({
    'version': torch.version.cuda,
    'seed': torch.cuda.initial_seed(),
    'device_count': torch.cuda.device_count(),
    'is_available': torch.cuda.is_available(),
    'allocated': torch.cuda.memory_allocated(),
    'reserved': torch.cuda.memory_reserved(),
    'devices': [props(d) for d in range(torch.cuda.device_count())]
})
$$ LANGUAGE plpython3u;

-- Trigger to create a model inference function after
-- creating a model entry.
CREATE FUNCTION ml.create_model_trigger()
RETURNS TRIGGER
AS $$
    from rikai.experimental.pg.model import create_model_trigger
    create_model_trigger(TD)
    return None
$$ LANGUAGE plpython3u;

CREATE TRIGGER create_model
AFTER INSERT ON ml.models
FOR EACH ROW
EXECUTE FUNCTION ml.create_model_trigger();


CREATE FUNCTION ml.train(
    name TEXT,
    model_type TEXT,
    tablename TEXT,
    columns TEXT[]
)
RETURNS BOOL
AS $$
    from rikai.experimental.pg.train import train
    return train(name, model_type, tablename, columns)
$$ LANGUAGE plpython3u;


CREATE FUNCTION ml.train(
    name TEXT,
    model_type TEXT,
    tablename TEXT,
    col TEXT
)
RETURNS BOOL
AS $$
    from rikai.experimental.pg.train import train
    return train(name, model_type, tablename, col)
$$ LANGUAGE plpython3u;

CREATE FUNCTION ml.train(
    name TEXT,
    model_type TEXT,
    tablename TEXT,
    col TEXT,
    options JSONB
)
RETURNS BOOL
AS $$
    from rikai.experimental.pg.train import train
    return train(name, model_type, tablename, col, options)
$$ LANGUAGE plpython3u;

-- Drop an model
CREATE FUNCTION ml.delete_model_trigger()
RETURNS TRIGGER
AS $$
BEGIN
	EXECUTE 'DROP FUNCTION IF EXISTS ml.' || OLD.name;
	RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_model
BEFORE DELETE ON ml.models
FOR EACH ROW
EXECUTE FUNCTION ml.delete_model_trigger();

-- User defined functions
CREATE FUNCTION iou(box1 box, box2 box)
RETURNS real
PARALLEL SAFE
AS $$ SELECT COALESCE(
	area(box1 # box2) / (area(box1) + area(box2) - area(box1 # box2)),
	0)
$$ LANGUAGE sql;
