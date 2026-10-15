from integrations.shopee_release_gate import ShopeeReleaseEvidence, evaluate_shopee_release


def test_default_blocks_every_gate():
    result = evaluate_shopee_release(ShopeeReleaseEvidence())
    assert result["ready"] is False
    assert len(result["blocked_by"]) == 7


def test_partial_evidence_does_not_release():
    result = evaluate_shopee_release(ShopeeReleaseEvidence(
        isolated_staging_db=True,
        effective_production_db_verified=True,
    ))
    assert result["ready"] is False
    assert "ATTRIBUTION_VERIFIED" in result["blocked_by"]


def test_all_verified_allows_release_review():
    result = evaluate_shopee_release(ShopeeReleaseEvidence(
        isolated_staging_db=True,
        effective_production_db_verified=True,
        affiliate_destination_verified=True,
        affiliate_attribution_verified=True,
        redirect_readonly_test_passed=True,
        staging_double_check_passed=True,
        explicit_release_approval=True,
    ))
    assert result == {"ready": True, "blocked_by": []}
