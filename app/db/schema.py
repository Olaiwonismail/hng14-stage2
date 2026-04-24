from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    MetaData,
    CheckConstraint,
    UniqueConstraint,
    text,
)

metadata = MetaData()

profiles_table = Table(
    "profiles",
    metadata,
    Column("id", String(36), primary_key=True),  # UUID v7 stored as string
    Column("name", String, nullable=False),
    Column("gender", String, nullable=False),
    Column("gender_probability", Float, nullable=False),
    Column("age", Integer, nullable=False),
    Column("age_group", String, nullable=False),
    Column("country_id", String(2), nullable=False),
    Column("country_name", String, nullable=False),
    Column("country_probability", Float, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=text("NOW()")),
    UniqueConstraint("name", name="uq_name"),
    CheckConstraint("gender IN ('male', 'female')", name="ck_gender"),
    CheckConstraint(
        "age_group IN ('child', 'teenager', 'adult', 'senior')", name="ck_age_group"
    ),
    CheckConstraint("length(country_id) = 2", name="ck_country_id_len"),
)

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_profiles_gender ON profiles (gender);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_age_group ON profiles (age_group);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_country_id ON profiles (country_id);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_age ON profiles (age);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_gender_probability ON profiles (gender_probability);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_country_probability ON profiles (country_probability);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles (created_at DESC);",
]


def create_all_tables(engine) -> None:
    """Create the profiles table and all performance indexes."""
    metadata.create_all(engine)
    with engine.connect() as conn:
        for stmt in _INDEXES:
            conn.execute(text(stmt))
        conn.commit()


def drop_all_tables(engine) -> None:
    """Drop all tables managed by this metadata instance."""
    metadata.drop_all(engine)
