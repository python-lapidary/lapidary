import typing as ty

import httpx

PageFlowGenT = ty.Generator[httpx.Request, httpx.Response, None]
