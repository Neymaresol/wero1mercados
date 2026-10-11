import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"scripts"/"check_db_config.py"
spec=importlib.util.spec_from_file_location("dbcheck",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_no_secret_leak():
    result=m.inspect({"DATABASE_URL":"postgresql://user:secret@example.org/example"})
    assert result == {"configured":True,"valid_format":True,"reason":"ok"}
    assert "secret" not in str(result)
def test_missing_url_fails():
    assert m.inspect({})["valid_format"] is False
