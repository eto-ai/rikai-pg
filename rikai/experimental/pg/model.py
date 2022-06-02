#  Copyright 2022 Rikai Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import Callable, Dict, Optional

import plpy
import torch
import torchvision
import torchvision.transforms as T
from rikai.parquet.dataset import convert_tensor
from rikai.spark.sql.codegen.dummy import DummyModelSpec
from rikai.spark.sql.codegen.fs import FileModelSpec
from rikai.spark.sql.model import ModelType
from rikai.types import Image
from torchvision.models.feature_extraction import create_feature_extractor


def schema_to_pg_types(schema: str) -> str:
    pass


class PgModel:
    """PostgreSQL Model"""

    def __init__(self, model_type: ModelType):
        self.model = model_type
        self.transform: Optional[Callable] = self.model.transform()

    def schema(self) -> str:
        return self.model.schema()

    def __repr__(self):
        return f"PGModel(model={self.model})"

    def predict(self, data):
        plpy.info(f"Predict data: {data}")
        data = convert_tensor(data)
        if self.transform:
            data = self.transform(data)
        preds = self.model([data])
        return preds[0]

        return [
            {
                "label": pred["label"],
                "label_id": pred["label_id"],
                "score": pred["score"],
                "box": (
                    (pred["box"].xmin, pred["box"].ymin),
                    (pred["box"].xmax, pred["box"].ymax),
                ),
            }
            for pred in preds
        ]


class PgEmbeddingModel:

    transform = T.Compose(
        [
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    def __init__(self):
        resnet = torchvision.models.resnet50(pretrained=True)
        self.model = create_feature_extractor(resnet, {"avgpool": "out"})
        self.model.eval()

    def schema(self) -> str:
        return "array<float>"

    def __repr__(self):
        return f"PgModel({self.model})"

    def predict(self, img):
        tensor = self.transform(Image(img["uri"]).to_numpy()).unsqueeze(0)

        with torch.no_grad():
            preds = self.model(tensor)
        embeddings = preds["out"][0, :].T[0][0].tolist()
        # pgvector only supports up to 1024 dimension for now
        return embeddings[:512]


def load_model(
    flavor: str,
    model_type: str,
    uri: Optional[str] = None,
    options: Optional[dict] = None,
) -> PgModel:
    if model_type == "features":
        return PgEmbeddingModel()

    # TODO: move load model into rikai core.
    conf = {
        "version": "1.0",
        "name": f"load_{model_type}",
        "flavor": flavor,
        "modelType": model_type,
        "uri": uri,
    }
    if uri:
        spec = FileModelSpec(conf)
    else:
        spec = DummyModelSpec(conf)
    model = spec.model_type
    model.load_model(spec)
    return PgModel(model)


def create_model_trigger(td: Dict):
    model_name = td["new"]["name"]
    plpy.info("Creating model: ", model_name)
    flavor = td["new"]["flavor"]
    model_type = td["new"]["model_type"]
    uri = td["new"].get("uri")

    model = load_model(flavor, model_type, uri)
    if uri is not None:
        # Quoted URI
        uri = "'{}'".format(uri)
    # TODO: this is hacking
    return_type = "real[]" if model_type in ("features", "pca") else "detection[]"
    args = "example real[]" if model_type in ("pca") else "example image"
    stmt = f"""CREATE FUNCTION ml.{model_name}({args})
RETURNS {return_type}
AS $BODY$
from rikai.experimental.pg.model import load_model
if 'model' not in SD:
    plpy.info('Loading model: flavor={flavor} type={model_type})')
    SD['model'] = load_model('{flavor}', '{model_type}', {uri})
return SD['model'].predict(example)
$BODY$ LANGUAGE plpython3u;"""
    plpy.execute(stmt)
