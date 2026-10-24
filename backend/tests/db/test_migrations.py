"""Tests for Alembic migrations single linear chain and upgrade/downgrade consistency (Owner: Anvi)."""

import os

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from alembic import command


@pytest.fixture
def alembic_cfg():
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    cfg = Config(ini_path)
    return cfg


def test_alembic_single_head_and_linear_history(alembic_cfg):
    """Ensures Alembic history remains a single linear chain with exactly one head."""
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected exactly 1 head revision, got {heads}"
    assert heads[0] == "0001_initial_schema"


def test_alembic_migration_upgrade_downgrade_cycle(alembic_cfg):
    """Tests executing full downgrade and re-upgrade on the live database."""
    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    script = ScriptDirectory.from_config(alembic_cfg)
    assert script.get_current_head() == "0001_initial_schema"
