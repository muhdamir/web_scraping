"""
The task is to scrape data from:
https://www.mudah.my/malaysia/cars-for-sale

Though we can scrape data from the page, but under the hood, it will call the the below API:
https://search.mudah.my/v1/search?category=1020&from=0&include=extra_images%2Cbody&limit=200&type=sell

we can inspect the API call in our browser.
* category=1020 stands for car, if we choose other category, it will give different value
* from=0 stands for from index 0
* limit=200 stands for how much we want to get the data, maximum is 200

"""

import pickle
from datetime import MAXYEAR, MINYEAR
from typing import Annotated

import pandas as pd
import requests
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    field_serializer,
    model_serializer,
)


class CustomBaseModel(BaseModel):
    """
    used a BaseModel
    """

    model_config = ConfigDict(
        extra="ignore",
        protected_namespaces=(),
    )


class MileageModel(CustomBaseModel):
    """
    Mileage of the car
    """

    gte: str
    lte: str


class AttributesModel(CustomBaseModel):
    """
    Attribute of the car
    """

    make_name: str = Field(serialization_alias="brand_name")
    model_name: str
    price: float
    manufactured_year: Annotated[
        int,
        Field(
            gte=MINYEAR,
            lte=MAXYEAR,
        ),
    ]
    mileage: MileageModel

    @field_serializer("mileage")
    def serialize_mileage(
        self,
        mileage: MileageModel,
        _info: SerializationInfo,
    ):
        return f"{mileage.gte} - {mileage.lte}"


class PostTypeModel(BaseModel):
    """
    Posting of the car in Mudah.my
    """

    attributes: AttributesModel

    @model_serializer
    def serialize_model(self):
        return self.attributes


class ResponseModel(BaseModel):
    """
    Mudah.my API response model
    """

    data: list[PostTypeModel]


query: dict[str, int | str] = {
    "category": 1020,
    "from": 0,
    "include": "extra_images,body",
    "limit": 200,
    "type": "sell",
}
res = requests.get(
    "https://search.mudah.my/v1/search",
    params=query,
    timeout=30,
)

data = ResponseModel.model_validate_json(res.text)
dict_data = data.model_dump(by_alias=True)

# save tabular data to csv
df = pd.DataFrame(dict_data["data"])
df.to_csv("data.csv", index=False)


# save dict data to pickle
with open(file="data.pkl", mode="+wb") as file:
    pickle.dump(dict_data, file=file)
