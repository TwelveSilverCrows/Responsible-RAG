"""
Tests for core data models — no external dependencies required.
These models are plain dataclasses that can be tested in isolation.
"""

import sys
import os

# Ensure backend/src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# ── Model Tests ──────────────────────────────────────────────────────────────

class TestSourceModel:
    """Test the Source dataclass in isolation."""

    def setup_method(self):
        """Import just the models module without the full API package."""
        # We import directly from the module path to avoid triggering
        # the full src.api.__init__ which imports fastapi
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "models",
            os.path.join(os.path.dirname(__file__), "..", "backend", "src", "api", "db", "models.py"),
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_source_defaults(self):
        Source = self.mod.Source
        s = Source()
        assert s.status == "queued"
        assert s.source_type == "pdf"
        assert s.title == ""

    def test_source_custom_values(self):
        Source = self.mod.Source
        s = Source(title="Test Doc", source_type="text", authors=["Author"], status="indexed")
        assert s.title == "Test Doc"
        assert s.source_type == "text"
        assert s.authors == ["Author"]
        assert s.status == "indexed"

    def test_source_to_dict(self):
        Source = self.mod.Source
        s = Source(title="Doc", source_type="pdf")
        d = s.to_dict()
        assert "id" in d
        assert d["title"] == "Doc"
        assert d["source_type"] == "pdf"

    def test_source_from_dict(self):
        Source = self.mod.Source
        original = Source(title="Test", source_type="pdf")
        d = original.to_dict()
        restored = Source.from_dict(d)
        assert restored.id == original.id
        assert restored.title == original.title

    def test_source_to_dict_skip_none(self):
        Source = self.mod.Source
        s = Source(title="Test", source_type="pdf")
        d = s.to_dict(skip_none=False)
        # When skip_none=False, all fields should be present
        assert "description" in d

    def test_source_to_dict_include_none(self):
        Source = self.mod.Source
        s = Source(title="Test", source_type="pdf", description=None)
        d = s.to_dict(skip_none=True)
        # When skip_none=True, None fields should be omitted
        assert "description" not in d


class TestSourceChunkModel:
    """Test the SourceChunk dataclass."""

    def setup_method(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "models",
            os.path.join(os.path.dirname(__file__), "..", "backend", "src", "api", "db", "models.py"),
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_chunk_defaults(self):
        SourceChunk = self.mod.SourceChunk
        c = SourceChunk(source_id="src-1", chunk_index=0, content="test")
        assert c.source_id == "src-1"
        assert c.chunk_index == 0
        assert c.content == "test"
        assert c.turbovec_id is None

    def test_chunk_to_dict(self):
        SourceChunk = self.mod.SourceChunk
        c = SourceChunk(source_id="src-1", chunk_index=0, content="test", turbovec_id="tv-1")
        d = c.to_dict()
        assert d["source_id"] == "src-1"
        assert d["turbovec_id"] == "tv-1"
        assert "id" in d


class TestHelperFunctions:
    """Test the module-level helper functions."""

    def setup_method(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "models",
            os.path.join(os.path.dirname(__file__), "..", "backend", "src", "api", "db", "models.py"),
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_now_iso_format(self):
        result = self.mod._now_iso()
        assert isinstance(result, str)
        assert "T" in result  # ISO-8601 format
        assert result.endswith("+00:00") or "+" in result  # timezone info

    def test_new_id_format(self):
        result = self.mod._new_id()
        assert isinstance(result, str)
        assert "-" in result  # UUID format
        assert len(result) == 36  # UUID4 length

    def test_new_id_unique(self):
        ids = {self.mod._new_id() for _ in range(100)}
        assert len(ids) == 100  # All unique


class TestOtherModels:
    """Test other dataclass models."""

    def setup_method(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "models",
            os.path.join(os.path.dirname(__file__), "..", "backend", "src", "api", "db", "models.py"),
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_user_model(self):
        User = self.mod.User
        u = User(email="test@example.com", display_name="Test User")
        assert u.email == "test@example.com"
        assert u.display_name == "Test User"
        assert u.role == "client"
        d = u.to_dict()
        assert d["email"] == "test@example.com"

    def test_conversation_model(self):
        Conversation = self.mod.Conversation
        c = Conversation(title="Test Chat", user_id="user-1")
        assert c.title == "Test Chat"
        assert c.message_count == 0
        d = c.to_dict()
        assert d["title"] == "Test Chat"

    def test_message_model(self):
        Message = self.mod.Message
        m = Message(conversation_id="conv-1", role="user", content="Hello")
        assert m.role == "user"
        assert m.content == "Hello"
        d = m.to_dict()
        assert d["conversation_id"] == "conv-1"

    def test_feedback_model(self):
        Feedback = self.mod.Feedback
        f = Feedback(feedback_type="thumbs_up", message_id="msg-1")
        assert f.feedback_type == "thumbs_up"
        d = f.to_dict()
        assert d["feedback_type"] == "thumbs_up"
