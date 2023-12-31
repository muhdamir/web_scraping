import logging
import os
import pickle
from datetime import MAXYEAR, MINYEAR
from typing import TYPE_CHECKING, Annotated, Literal

import pandas as pd
import requests
from lxml import html
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_serializer

# setup logger
logging.basicConfig(
    format="{asctime} - {levelname}: {name}.{funcName} - {message}",
    style="{",
)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


class CustomBaseModel(BaseModel):
    """
    custom base model class to replace base model class
    """

    model_config = ConfigDict(extra="ignore")


class MileageModel(CustomBaseModel):
    gte: int
    lte: int

    @model_serializer
    def serialize_model(self) -> str:
        return f"{self.gte} - {self.lte}"


class AttributesModel(CustomBaseModel):
    manufacturedYear: Annotated[
        int,
        Field(
            gte=MINYEAR,
            lte=MAXYEAR,
            serialization_alias="manufactured_year",
        ),
    ]
    mileage: MileageModel
    modelName: str = Field(serialization_alias="model_name")
    makeName: str = Field(serialization_alias="brand_name")
    price: float


class IntIdModel(CustomBaseModel):
    attributes: AttributesModel


def porcess(val: dict[int, IntIdModel]):
    return list(val.values())


CustomType2 = Annotated[IntIdModel, AfterValidator(lambda x: x.attributes)]
ByID = Annotated[dict[int, CustomType2], AfterValidator(porcess)]


class AdListingModel(CustomBaseModel):
    byID: ByID

    if TYPE_CHECKING:
        byID: list[IntIdModel]  # type: ignore


class InitialStateModel(CustomBaseModel):
    adListing: AdListingModel


class PropsModel(CustomBaseModel):
    initialState: InitialStateModel


class JsonDataModel(CustomBaseModel):
    props: PropsModel

    @model_serializer
    def serialize_model(self):
        return self.props.initialState.adListing.byID


def main(
    file_type: Literal["pickle", "csv"] = "csv",
):
    logger.info("✅  application started")
    logger.info("⚒️  requesting to mudah.my's website...")
    # request
    res = requests.get(
        "https://www.mudah.my/malaysia/cars-for-sale?o=1",
        timeout=30,
    )
    if res.status_code != 200:
        logger.error("❌  get request failed")
        return

    # html docs
    docs = html.fromstring(res.text)

    # extract raw data
    raw_data = docs.xpath(
        """normalize-space(//script[@type="application/json"]/text())"""
    )
    raw_data = str(raw_data)

    # expected raw_data is a string json
    if not isinstance(raw_data, str):
        return

    # validate with pydantic
    proper_data = JsonDataModel.model_validate_json(raw_data)
    data = JsonDataModel.model_dump(proper_data, by_alias=True)

    match file_type:
        case "csv":
            logger.info("⚒️  saving to a csv file")
            df = pd.DataFrame(data)
            df.to_csv("data.csv", index=False)
            message = f"✅  data is saved in {os.path.join(os.getcwd(), 'data.csv')}"
            logger.info(message)

        case "pickle":
            # save dict data to pickle
            logger.info("⚒️  saving to a pickle file")
            with open(file="data.pkl", mode="+wb") as file:
                pickle.dump(data, file=file)
            message = f"✅  data is saved in {os.path.join(os.getcwd(), 'data.pkl')}"
            logger.info(message)

        case _:
            logger.warning("⚠️  wrong argument. Data is not saved")

    # save
    with open(".hahah.txt", mode="+w", encoding="utf-8") as file:
        file.write(JsonDataModel.model_dump_json(proper_data, by_alias=True))


if __name__ == "__main__":
    main()
