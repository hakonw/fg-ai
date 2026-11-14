from pydantic import BaseModel, Field
from robyn import Request

class RequestModel(BaseModel):
    max_images: int = Field(100, ge=1, le=1000)
    score_threshold: float = Field(0.3, ge=0.0, le=1.0)

    @classmethod
    def of(cls, request: Request) -> 'RequestModel':
        raw = {}
        for key in cls.model_fields:
            value = request.form_data.get(key) or request.query_params.get(key)
            if value is not None:
                raw[key] = value
        return cls.model_validate(raw)
