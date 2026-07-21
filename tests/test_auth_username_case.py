import importlib
import sys
import types
from pathlib import Path

from tests.helpers.import_state import clear_module


def _real_core_package():
    root = Path(__file__).resolve().parent.parent
    core_path = str(root / "core")
    core = sys.modules.get("core")
    if core is None:
        core = types.ModuleType("core")
        sys.modules["core"] = core
    core.__path__ = [core_path]
    clear_module("core.auth")
    return core


def _auth_module():
    _real_core_package()
    return importlib.import_module("core.auth")


def _make_manager(tmp_path):
    auth_mod = _auth_module()
    auth_mod._hash_password = lambda password: f"hash:{password}"
    auth_mod._verify_password = lambda password, hashed: hashed == f"hash:{password}"
    auth_path = tmp_path / "auth.json"
    mgr = auth_mod.AuthManager(str(auth_path))
    return mgr


def test_username_casing_preserved(tmp_path):
    mgr = _make_manager(tmp_path)
    
    # 1. Test create_user preserves casing
    assert mgr.create_user("Jariz", "password123") is True
    assert "jariz" in mgr.users
    assert mgr.users["jariz"]["username"] == "Jariz"
    
    # 2. Test status returns case-preserved username
    token = mgr.create_session_trusted("jariz")
    stat = mgr.status(token)
    assert stat["username"] == "Jariz"
    
    # 3. Test list_users returns case-preserved username
    users_list = mgr.list_users()
    assert any(u["username"] == "Jariz" for u in users_list)
    
    # 4. Test rename_user with case-only change preserves casing
    # (Since rename_user in AuthManager checks if requester is admin)
    mgr.users["jariz"]["is_admin"] = True
    assert mgr.rename_user("jariz", "JARIZ", "jariz") is True
    assert "jariz" in mgr.users
    assert mgr.users["jariz"]["username"] == "JARIZ"
    
    # 5. Test status returns new casing
    stat2 = mgr.status(token)
    assert stat2["username"] == "JARIZ"
