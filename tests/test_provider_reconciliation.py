import hashlib
import pytest
from provider_reconciliation import Provenance, official_adapter, reconcile

COLUMNS = {"external_id": "id", "status": "state", "sale_amount_brl": "sale", "commission_brl": "fee"}
RAW = b"id,state,sale,fee\\norder-1,confirmed,120.00,12.00\\n".replace(b"\\n", b"\n")

def provenance(partner="amazon", verified=True, digest=None):
    return Provenance(partner, "account-1", "report-20261012", digest or hashlib.sha256(RAW).hexdigest(), verified)

@pytest.mark.parametrize("partner", ["amazon", "shopee", "mercado_livre"])
def test_all_three_adapters(partner):
    rows = official_adapter(partner, RAW, provenance(partner), COLUMNS)
    assert rows[0]["status"] == "confirmed"
    assert rows[0]["commission_brl"] == "12.00"

def test_rejects_unverified_source():
    with pytest.raises(ValueError):
        official_adapter("amazon", RAW, provenance(verified=False), COLUMNS)

def test_rejects_modified_report():
    with pytest.raises(ValueError):
        official_adapter("amazon", RAW + b"extra", provenance(), COLUMNS)

def test_rejects_partner_mismatch():
    with pytest.raises(ValueError):
        official_adapter("shopee", RAW, provenance(), COLUMNS)

def test_rejects_duplicate_in_report():
    data = RAW + b"order-1,confirmed,120.00,12.00\n"
    with pytest.raises(ValueError):
        official_adapter("amazon", data, provenance(digest=hashlib.sha256(data).hexdigest()), COLUMNS)

def test_idempotent_same_state():
    item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
    assert reconcile(item, item) == item

@pytest.mark.parametrize("terminal", ["reversed", "cancelled"])
def test_terminal_not_revived(terminal):
    item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
    with pytest.raises(ValueError):
        reconcile({**item, "status": terminal}, item)

def test_confirmed_can_be_reversed():
    item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
    assert reconcile(item, {**item, "status": "reversed"})["status"] == "reversed"

def test_confirmed_cannot_regress_to_pending():
    item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
    with pytest.raises(ValueError):
        reconcile(item, {**item, "status": "pending"})

def test_rejects_same_status_changed_commission():
    item = official_adapter("amazon", RAW, provenance(), COLUMNS)[0]
    with pytest.raises(ValueError):
        reconcile(item, {**item, "commission_brl": "99.00"})
