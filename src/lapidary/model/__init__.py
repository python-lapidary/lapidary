import pydantic


class ModelBase(pydantic.BaseModel):
    """A simple base class for request and response models. Pydantic's BaseModel with defaults suitable for typical cases."""

    model_config = pydantic.ConfigDict(
        extra='allow',
        populate_by_name=True,
    )
