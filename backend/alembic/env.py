from alembic import context

# Migration metadata is introduced with the first data model in phase 2.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(url=context.config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    raise RuntimeError("No migrations exist yet; phase 2 introduces the initial schema.")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
