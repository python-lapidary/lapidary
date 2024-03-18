import pydantic


class ModelBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra='allow',
        populate_by_name=True,
    )
