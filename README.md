# Postgres Rikai Extension

Status: Proof of concept

```sh
pip install rikai
make install
```

## Usage

To load `rikai` PostgreSQL extension

```sql
CREATE EXTENSION plpython3u;
CREATE EXTENSION rikai;
```

Create a model via `INSERT INTO`

```sql
INSERT INTO ml.models
(name, flavor, model_type, uri)
VALUES
('cat_detector', 'pytorch', 'ssd', 's3://bucket/to/cat.pth')
```

A function `ml.<model_name>` will be created after model insertation.

To use the registered model for inference:

```sql
SELECT ml.cat_detector(image) FROM cat_dataset
```

Show all registered models:

```sql
SELECT * FROM ml.models;
```

## Local development

```sh
# Build and run docker image, prepare testing data and load a model.
$ make run

# Connect to postgres

$ psql -h localhost -U postgres
```

## TODOs

- [ ] Support classification models
- [ ] Release and installation

## Limitations

- `rikai` needs to be installed with the system python.
- Batch inference.
- Not ready for production yet.
