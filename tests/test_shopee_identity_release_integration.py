from integrations.db_identity_doublecheck import safe_connection_identity, verify_isolation
from integrations.shopee_release_gate import ShopeeReleaseEvidence, evaluate_shopee_release


def test_same_database_blocks_shopee():
    prod = safe_connection_identity("postgresql://user:pass@shared.example/app", "production")
    stage = safe_connection_identity("postgresql://user:pass@shared.example/app", "staging")
    isolated = verify_isolation(prod, stage)["isolated"]
    evidence = ShopeeReleaseEvidence(isolated_staging_db=isolated,
        effective_production_db_verified=True,
        affiliate_destination_verified=True,
        affiliate_attribution_verified=True,
        redirect_readonly_test_passed=True,
        staging_double_check_passed=True,
        explicit_release_approval=True)
    assert evaluate_shopee_release(evidence)["ready"] is False


def test_distinct_database_alone_never_approves_shopee():
    prod = safe_connection_identity("postgresql://user:pass@prod.example/app", "production")
    stage = safe_connection_identity("postgresql://user:pass@stage.example/app", "staging")
    isolated = verify_isolation(prod, stage)["isolated"]
    assert isolated
    evidence = ShopeeReleaseEvidence(isolated_staging_db=isolated)
    result = evaluate_shopee_release(evidence)
    assert result["ready"] is False
    assert "ATTRIBUTION_VERIFIED" in result["blocked_by"]
