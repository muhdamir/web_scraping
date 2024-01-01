"""
🚀  MySQL Task
Design a schema that accommodates the extracted data, and write a Python script to:
- Connect to the database
- Create the necessary tables
- Insert the scraped car information into the database
- Include error handling mechanisms to manage potential issues during the database operations.
"""

import logging
import os
from datetime import datetime
from typing import TypeVar, Union

import pandas as pd
from pydantic import BaseModel, ConfigDict, RootModel
from sqlalchemy import Engine, ForeignKey, UniqueConstraint, create_engine, func
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

# setup logger
logging.basicConfig(
    format="{asctime} - {levelname}: {name}.{funcName} - {message}",
    style="{",
)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


# tables
class Base(DeclarativeBase):
    pass


class CarBrand(Base):
    __tablename__ = "car_brand"

    car_brand_id: Mapped[int] = mapped_column(primary_key=True)
    car_brand_name: Mapped[str] = mapped_column(
        VARCHAR(45),
        nullable=False,
        unique=True,
    )
    car_brand_created_at: Mapped[datetime] = mapped_column(
        default=func.now(),  # pylint: disable=not-callable
    )
    car_brand_updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    # relationship
    car_models: Mapped[list["CarModel"]] = relationship(
        back_populates="car_brand",
        cascade="all, delete-orphan",
    )


class CarModel(Base):
    __tablename__ = "car_model"

    car_model_id: Mapped[int] = mapped_column(primary_key=True)
    car_model_name: Mapped[str] = mapped_column(VARCHAR(45), nullable=False)
    car_brand_id: Mapped[int] = mapped_column(
        ForeignKey("car_brand.car_brand_id", ondelete="CASCADE")
    )
    car_model_created_at: Mapped[datetime] = mapped_column(
        default=func.now(),  # pylint: disable=not-callable
    )
    car_model_updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    # relationship
    car_brand: Mapped[CarBrand] = relationship(
        back_populates="car_models",
    )
    car_info: Mapped[list["CarInfo"]] = relationship(
        back_populates="car_model",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "car_model_name",
            "car_model_id",
        ),
    )


class CarInfo(Base):
    __tablename__ = "car_info"

    car_info_id: Mapped[int] = mapped_column(primary_key=True)
    car_manufactured_year: Mapped[int] = mapped_column(nullable=False)
    car_mileage: Mapped[str] = mapped_column(VARCHAR(45), nullable=False)
    car_price: Mapped[float] = mapped_column(nullable=False)
    car_model_id: Mapped[int] = mapped_column(
        ForeignKey("car_model.car_model_id", ondelete="CASCADE")
    )

    # relationship
    car_model: Mapped[CarModel] = relationship(back_populates="car_info")


# db config
engine = create_engine(
    url="mysql+mysqldb://admin:secret@localhost:8083/dev",
    # echo=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
)


class BrandModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    # attribute
    car_brand_id: int
    car_brand_name: str
    # car_brand_created_at: datetime
    # car_brand_updated_at: datetime


class ModelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    car_model_id: int
    car_model_name: str


T = TypeVar("T")
GenericModelResponse = RootModel[Union[list[T], T]]


def create_table(
    target_base: type[DeclarativeBase] = Base,
    target_engine: Engine = engine,
):
    logger.info("⚒️  creating tables...")
    target_base.metadata.create_all(bind=target_engine)
    logger.info("✅  all tables are successfully created")


def migrate():
    logger.info("⚒️  reading csv file...")
    if not "data.csv" in os.listdir():
        logger.warning(
            "⚠️  data migration will not be executed, please run scraper script first"
        )
        return

    logger.info("⚒️  running migration...")
    # read csv
    df = pd.read_csv("data.csv")

    # create brand
    all_brand = df["brand_name"].unique()
    with SessionFactory() as session:
        logger.info("⚒️  updating car brand data...")
        all_brand = [
            CarBrand(car_brand_name=brand)
            for brand in all_brand
            if not session.query(CarBrand)
            .filter(CarBrand.car_brand_name == brand)
            .all()
        ]

        if all_brand:
            session.add_all(all_brand)
            session.commit()
            # for brand in all_brand:
            #     session.refresh(brand)
            logger.info("✅  all car brands are up to date")

        else:
            logger.info("✅  nothing to update for car brands")

        all_brand = session.query(CarBrand).all()

        # create model
        logger.info("⚒️  updating car model data...")
        updated_brand = GenericModelResponse[BrandModel].model_validate(all_brand)
        data_dict = updated_brand.model_dump()
        data_dict = dict([(i["car_brand_name"], i["car_brand_id"]) for i in data_dict])

        df["brand_name"] = df["brand_name"].replace(data_dict)
        target_model = (
            df.groupby(["brand_name", "model_name"])
            .size()
            .reset_index()[["brand_name", "model_name"]]
            .rename(
                columns={"brand_name": "car_brand_id", "model_name": "car_model_name"}
            )
        )

        target_model_list = target_model.to_dict(orient="records")
        all_model = [
            CarModel(**i)
            for i in target_model_list
            if not session.query(CarModel)
            .filter(CarModel.car_model_name == i["car_model_name"])
            .all()
        ]

        if all_model:
            session.add_all(all_model)
            session.commit()
            # for model in all_model:
            #     session.refresh(model)
            logger.info("✅  all car models are up to date")

        else:
            logger.info("✅  nothing to update for car models")

        all_model = session.query(CarModel).all()

        # create car
        logger.info("⚒️  updating car info data...")
        updated_model = GenericModelResponse[ModelModel].model_validate(all_model)
        data_dict = updated_model.model_dump()
        data_dict = dict([(i["car_model_name"], i["car_model_id"]) for i in data_dict])

        df["model_name"] = df["model_name"].replace(data_dict)
        target_car = (
            df[["model_name", "price", "manufactured_year", "mileage"]]
            .rename(columns={"model_name": "model_id"})
            .add_prefix("car_")
            .to_dict(orient="records")
        )
        all_car = [
            CarInfo(**i)
            for i in target_car
            if not session.query(CarInfo).filter_by(**i).all()
        ]

        if all_car:
            session.add_all(all_car)
            session.commit()
            # for car in all_car:
            #     session.refresh(car)
            logger.info("✅  all car info are up to date")
            return
        logger.info("✅  nothing to update for car info")


def main():
    logger.info("✅  application started")
    create_table()
    migrate()


if __name__ == "__main__":
    main()
