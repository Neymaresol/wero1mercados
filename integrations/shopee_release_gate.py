"""Fail-closed commercial release gate for Shopee affiliate offers.

No network calls, database writes, or inferred attribution.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ShopeeReleaseEvidence:
    isolated_staging_db: bool = False
    effective_production_db_verified: bool = False
    affiliate_destination_verified: bool = False
    affiliate_attribution_verified: bool = False
    redirect_readonly_test_passed: bool = False
    staging_double_check_passed: bool = False
    explicit_release_approval: bool = False


def evaluate_shopee_release(evidence: ShopeeReleaseEvidence) -> dict:
    checks = {
        "STAGING_DB_ISOLATED": evidence.isolated_staging_db,
        "PRODUCTION_DB_VERIFIED": evidence.effective_production_db_verified,
        "DESTINATION_VERIFIED": evidence.affiliate_destination_verified,
        "ATTRIBUTION_VERIFIED": evidence.affiliate_attribution_verified,
        "REDIRECT_TEST_PASSED": evidence.redirect_readonly_test_passed,
        "STAGING_DOUBLE_CHECK_PASSED": evidence.staging_double_check_passed,
        "RELEASE_APPROVED": evidence.explicit_release_approval,
    }
    blocked = [key for key, passed in checks.items() if passed is not True]
    return {"ready": not blocked, "blocked_by": blocked}
