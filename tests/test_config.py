from backend.src.core.config import _normalize_mongo_uri, _is_running_in_docker


def test_normalize_mongo_uri_keeps_non_localhost_values(monkeypatch):
    monkeypatch.setattr("backend.src.core.config._is_running_in_docker", lambda: True)
    assert _normalize_mongo_uri("mongodb://rag:ragpassword@mongo:27017/db") == "mongodb://rag:ragpassword@mongo:27017/db"


def test_normalize_mongo_uri_rewrites_localhost_for_docker(monkeypatch):
    monkeypatch.setattr("backend.src.core.config._is_running_in_docker", lambda: True)
    assert _normalize_mongo_uri("mongodb://rag:ragpassword@localhost:27017/db") == "mongodb://rag:ragpassword@mongo:27017/db"


def test_normalize_mongo_uri_leaves_non_docker_unchanged(monkeypatch):
    monkeypatch.setattr("backend.src.core.config._is_running_in_docker", lambda: False)
    assert _normalize_mongo_uri("mongodb://rag:ragpassword@localhost:27017/db") == "mongodb://rag:ragpassword@localhost:27017/db"
