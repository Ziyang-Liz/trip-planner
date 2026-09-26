from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class TripHistory(Base):
    __tablename__ = "trip_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    origin: Mapped[str] = mapped_column(String(120), index=True)
    destination: Mapped[str] = mapped_column(String(120), index=True)

    # optional parameters used during planning
    poi_limit: Mapped[int] = mapped_column(Integer)

    route_distance_km: Mapped[float] = mapped_column(Float)
    route_duration_min: Mapped[float] = mapped_column(Float)

    # full response from your /demo/plan (as JSONB)
    plan_json = mapped_column(JSONB)
