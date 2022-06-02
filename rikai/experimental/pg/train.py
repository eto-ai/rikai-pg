#

import json
import pickle
import uuid
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np
import plpy
from sklearn.decomposition import PCA

DEFAULT_PCA_COMPONENTS = 2


def train_pca(
    table: str, columns: Union[str, list[str]], options: Dict[str, any]
) -> str:
    if isinstance(columns, list):
        raise ValueError("Bad column")
    results = plpy.execute(f"SELECT {columns} FROM {table}")

    arr = np.array([results[i][columns] for i in range(results.nrows())])
    pca = PCA(n_components=options.get("components", DEFAULT_PCA_COMPONENTS))
    pca.fit(arr)

    # TODO: log model
    model_uri = Path("/tmp/models/pca/") / f"{uuid.uuid4()}.pth"
    model_uri.parent.mkdir(parents=True, exist_ok=True)
    with model_uri.open("wb") as fobj:
        pickle.dump(pca, fobj)
    return str(model_uri)


def train(
    name: str,
    model_type: str,
    table: str,
    columns: Union[str, list[str]],
    options: Optional[Dict] = None,
):
    plpy.info(f"Training model {name}: flavor=sklearn type={model_type}")
    try:
        train_routine = SUPPORTED_MODEL_TYPES[model_type]
        uri = train_routine(table, columns, options)
    except KeyError:
        plpy.info("Only PCA model is supported")
        return False
    plpy.execute(
        f"""
        INSERT INTO ml.models (name, flavor, model_type, uri, options)
            VALUES (
                '{name}',
                'sklearn',
                '{model_type}',
                '{uri}',
                '{json.dumps(options)}'::json
            );
    """
    )
    return True


SUPPORTED_MODEL_TYPES = {
    "pca": train_pca,
}
