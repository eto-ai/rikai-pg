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

import json
from typing import Any, Callable, Dict, Optional

import torch
import torchvision
import torchvision.transforms as T
from rikai.parquet.dataset import convert_tensor
from rikai.pytorch.models.torch import ClassificationModelType, ObjectDetectionModelType
from rikai.pytorch.models.feature_extractor import FeatureExtractorType
from rikai.spark.sql.codegen.dummy import DummyModelSpec
from rikai.spark.sql.codegen.fs import FileModelSpec
from rikai.spark.sql.model import ModelType
from rikai.types import Image
from torchvision.models.feature_extraction import create_feature_extractor

from .logging import info
from .schema import parse_schema


class PgModel:
    """PostgreSQL Model"""

    def __init__(self, model_type: ModelType):
        self.model = model_type
        self.transform: Optional[Callable] = self.model.transform()

        self._is_vision_type = isinstance(
            self.model,
            (ClassificationModelType, ObjectDetectionModelType, FeatureExtractorType),
        )

    def schema(self) -> str:
        return self.model.schema()

    def args(self) -> str:
        """Postgres UDF argument string"""
        if self._is_vision_type:
            return "example image"
        else:
            return "example real[]"

    def __repr__(self):
        return f"PGModel(model={self.model})"

    def _pg_to_rikai(self, data) -> Any:
        if self._is_vision_type:
            return Image(data["uri"])
        return data

    def predict(self, data):
        data = self._pg_to_rikai(data)
        data = convert_tensor(data)
        if self.transform:
            data = self.transform(data)
        preds = self.model(data.unsqueeze(0))
        return preds[0]


def load_model(
    flavor: str,
    model_type: str,
    uri: Optional[str] = None,
    options: Optional[dict] = None,
) -> PgModel:
    conf = {
        "version": "1.0",
        "name": f"load_{model_type}",
        "flavor": flavor,
        "modelType": model_type,
        "uri": uri,
        "options": options,
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
    info("Creating model: {model_name}")
    flavor = td["new"]["flavor"]
    model_type = td["new"]["model_type"]
    uri = td["new"].get("uri")
    options = json.loads(td["new"].get("options", "{}"))

    import plpy

    model = load_model(flavor, model_type, uri, options)
    if uri is not None:
        # Quoted URI
        uri = "'{}'".format(uri)
    return_type = parse_schema(model.schema())
    stmt = f"""CREATE FUNCTION ml.{model_name}({model.args()})
RETURNS {return_type}
AS $BODY$
from rikai.experimental.pg.model import load_model
if 'model' not in SD:
    plpy.info('Loading model: flavor={flavor} type={model_type})')
    SD['model'] = load_model('{flavor}', '{model_type}', {uri}, {options})
return SD['model'].predict(example)
$BODY$ LANGUAGE plpython3u;"""
    plpy.execute(stmt)
