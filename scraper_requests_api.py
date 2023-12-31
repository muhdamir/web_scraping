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

import logging
import os
import pickle
from datetime import MAXYEAR, MINYEAR
from typing import Annotated, Literal

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

# setup logger
logging.basicConfig(
    format="{asctime} - {levelname}: {name}.{funcName} - {message}",
    style="{",
)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


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


def main(
    file_type: Literal["pickle", "csv"] = "csv",
):
    logger.info("✅  application started")

    query: dict[str, str | int] = {
        "category": 1020,
        "from": 0,
        "include": "extra_images,body",
        "limit": 200,
        "type": "sell",
    }
    logger.info("⚒️  requesting to mudah.my's API...")
    res = requests.get(
        "https://search.mudah.my/v1/search",
        params=query,
        timeout=30,
    )
    if res.status_code != 200:
        logger.error("❌  get request failed")
        return

    logger.info("✅  get request is successfull")
    data_preview = f"🔎  preview of the data: {res.text[:35]}..."
    logger.info(data_preview)

    data = ResponseModel.model_validate_json(res.text)
    dict_data = data.model_dump(by_alias=True)

    match file_type:
        case "csv":
            # save tabular data to csv
            logger.info("⚒️  saving to a csv file")
            df = pd.DataFrame(dict_data["data"])
            df.to_csv("data.csv", index=False)
            message = f"✅  data is saved in {os.path.join(os.getcwd(), 'data.csv')}"
            logger.info(message)

        case "pickle":
            # save dict data to pickle
            logger.info("⚒️  saving to a pickle file")
            with open(file="data.pkl", mode="+wb") as file:
                pickle.dump(dict_data, file=file)
            message = f"✅  data is saved in {os.path.join(os.getcwd(), 'data.pkl')}"
            logger.info(message)

        case _:
            logger.warning("⚠️  wrong argument. Data is not saved")


if __name__ == "__main__":
    main(file_type="pickle")
