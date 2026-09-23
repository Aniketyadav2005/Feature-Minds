from pydantic import BaseModel, Field


class BatchPdfRequest(BaseModel):
    analysis_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=20,
    )