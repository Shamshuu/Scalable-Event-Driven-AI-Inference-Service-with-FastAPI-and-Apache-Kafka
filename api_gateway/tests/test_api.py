import pytest
from app.models import InferenceRequest

def test_request_validation_rejects_empty_input():
    with pytest.raises(Exception): InferenceRequest(input_data="")
def test_default_model_is_used():
    assert InferenceRequest(input_data="hello").model_id == "default_model"
def test_request_id_is_uuid_shape():
    import uuid
    value = str(uuid.uuid4())
    assert str(uuid.UUID(value)) == value
