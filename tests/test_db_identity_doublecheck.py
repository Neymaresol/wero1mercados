from integrations.db_identity_doublecheck import safe_connection_identity, verify_isolation


def test_no_secrets_exposed():
    value = safe_connection_identity("postgresql://secretuser:secretpassword@db.example:5432/app", "staging")
    assert value["configured"]
    assert "secret" not in str(value)
    assert "db.example" not in str(value)


def test_password_change_same_identity():
    a = safe_connection_identity("postgresql://u:first@db.example/app", "production")
    b = safe_connection_identity("postgresql://u:second@db.example:5432/app", "staging")
    assert not verify_isolation(a, b)["isolated"]


def test_different_databases_isolated():
    a = safe_connection_identity("postgresql://u:p@prod.example/app", "production")
    b = safe_connection_identity("postgresql://u:p@stage.example/app", "staging")
    assert verify_isolation(a, b)["isolated"]


def test_missing_or_invalid_fail_closed():
    a = safe_connection_identity("", "production")
    b = safe_connection_identity("postgresql://u:p@stage.example/app", "staging")
    assert not verify_isolation(a, b)["isolated"]
    assert safe_connection_identity("sqlite:///tmp/a.db")["identity"] is None
