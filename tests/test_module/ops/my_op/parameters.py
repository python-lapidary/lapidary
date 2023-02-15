from pydantic import BaseModel


class my_param(BaseModel):
    myProp: str


class param_b(BaseModel):
    param_ba: str
    param_bb: str
