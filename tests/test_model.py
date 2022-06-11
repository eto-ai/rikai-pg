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

from pathlib import Path

import pytest
import torch
import torchvision
from rikai.pytorch.models.feature_extractor import FeatureExtractor

from rikai.experimental.pg.model import load_model


@pytest.fixture(scope="session")
def resnet_path(tmp_path_factory: Path) -> Path:
    model = torchvision.models.resnet50()

    model_path = tmp_path_factory.mktemp("models") / "resnet.pth"
    torch.save(model, model_path)
    return model_path


@pytest.fixture(scope="session")
def resnet_features_path(tmp_path_factory: Path, resnet_path: Path) -> Path:
    resnet = torch.load(resnet_path)
    features_path = tmp_path_factory.mktemp("models") / "resnet_features.pth"
    model = FeatureExtractor(resnet, node="avgpool")
    torch.save(model, features_path)
    return features_path


def test_load_model():
    model = load_model("pytorch", "ssd")
    model.predict(
        {"uri": "http://farm2.staticflickr.com/1129/4726871278_4dd241a03a_z.jpg"}
    )


def test_embedding(resnet_features_path):
    model = load_model(
        "pytorch",
        "feature_extractor",
        uri=str(resnet_features_path),
        options={"model_type": "resnet"},
    )
    with torch.no_grad():
        print(model)
        model.predict(
            {"uri": "http://farm2.staticflickr.com/1129/4726871278_4dd241a03a_z.jpg"}
        )
