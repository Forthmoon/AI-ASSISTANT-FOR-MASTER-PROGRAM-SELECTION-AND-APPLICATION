from pydantic import BaseModel, Field

class RecommendationInput(BaseModel):
    preferred_subject: str = Field(..., description="The subject you want to study")
    bachelor_major: str = Field(..., description="Your undergraduate major")
    country: str = Field(..., description="Your nationality (Where you come from)")
    ielts_score: float | None = Field(None, description="IELTS score")
    toefl_score: float | None = Field(None, description="TOEFL score")
    gmat_score: float | None = Field(None, description="GMAT score")
    gre_score: float | None = Field(None, description="GRE score")
    alt_cert: str | None = Field(None, description="Alternative certificate")
    city_preference: str | None = Field(None, description="City or Region preference (where you want to study)")
    tuition_fee: float | None = Field(None, description="Tuition fee budget")
    duration: int | None = Field(None, description="Preferred duration of study")
    qs_ranking: str | None = Field(None, description="Preferred QS university ranking")
    qs_subject_ranking: str | None = Field(None, description="Preferred QS subject ranking")
    max_results: int | None = Field(None, description="Number of results to return")
