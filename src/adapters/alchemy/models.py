import sqlalchemy as sa

sa_metadata = sa.MetaData()
users = sa.Table(
    "users",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("outer_id", sa.String, unique=True),
    sa.Column("nickname", sa.String, nullable=True),
    sa.Column("name", sa.String, nullable=True),
    sa.Column("surname", sa.String, nullable=True),
    sa.Column("patronymic", sa.String, nullable=True),
    sa.Column("current_scenario_name", sa.String, nullable=True),
    sa.Column("current_node_id", sa.String, nullable=True),
)
user_contexts = sa.Table(
    "user_contexts",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user", sa.ForeignKey("users.id", ondelete="CASCADE")),
    sa.Column("ctx", sa.JSON, default={}),  # TODO: переделать на отдельные колонки
)
out_messages = sa.Table(
    "out_messages",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user", sa.ForeignKey("users.id", ondelete="CASCADE")),
    sa.Column("node_id", sa.String),
    sa.Column("message_id", sa.String),
)
projects = sa.Table(
    "projects",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String, unique=True),
)
scenarios = sa.Table(
    "scenarios",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("project", sa.ForeignKey("projects.name", ondelete="CASCADE")),
    sa.Column("name", sa.String),
    sa.Column("scenario_json", sa.JSON),
)
scenario_texts = sa.Table(
    "scenario_texts",
    sa_metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("scenario", sa.ForeignKey("scenarios.id", ondelete="CASCADE")),
    sa.Column("project", sa.ForeignKey("projects.name", ondelete="CASCADE")),
    sa.Column("template_name", sa.String),
    sa.Column("template_value", sa.String),
)
