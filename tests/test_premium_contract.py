from pathlib import Path
import ast

source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text()
ast.parse(source)

def test_premium_routes_are_admin_only():
    assert 'def premium_status(_admin: None = Depends(require_admin)):' in source
    assert 'payload: PremiumSettingUpdate, _admin: None = Depends(require_admin)' in source

def test_premium_is_isolated_and_audited():
    assert 'CREATE TABLE IF NOT EXISTS premium_settings' in source
    assert 'CREATE TABLE IF NOT EXISTS premium_change_log' in source
    assert 'operational_effect":"registry_only"' in source
    assert '"campaign_publication": {"approval_required"}' in source
