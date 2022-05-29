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

from typing import Optional

import torch
import torchvision
import torchvision.transforms as T
from torchvision.models.feature_extraction import create_feature_extractor

from rikai.spark.sql.codegen.dummy import DummyModelSpec
from rikai.spark.sql.codegen.fs import FileModelSpec
from rikai.spark.sql.model import ModelType
from rikai.types import Image


class PgModel:
    """Postgres Model"""
    def __init__(self, model_type: ModelType):
        self.model = model_type

    def __repr__(self):
        return f"PgModel({self.model})"

    def predict(self, img):
        tensor = torch.tensor(
            self.model.transform()(Image(img["uri"]).to_numpy())
        )
        preds = self.model.predict([tensor])[0]

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

transform = T.Compose(
            [
                T.ToTensor(),
                T.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

class PgEmbeddingModel:
    def __init__(self):
        resnet = torchvision.models.resnet50(pretrained=True)
        self.model = create_feature_extractor(resnet, {"avgpool": "out"})
        self.model.eval()

    def __repr__(self):
        return f"PgModel({self.model})"

    def predict(self, img):
        tensor = transform(Image(img["uri"]).to_numpy()).unsqueeze(0)

        print(tensor)
        with torch.no_grad():
            preds = self.model(tensor)
        print(preds["out"].shape, preds["out"])
        embeddings = preds["out"][0, :].T[0][0].tolist()
        print(embeddings, type(embeddings), type(embeddings[0]))
        return embeddings


def load_model(
    flavor: str,
    model_type: str,
    uri: Optional[str] = None,
    options: Optional[dict] = None
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
