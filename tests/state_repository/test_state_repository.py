import pytest

from ttflow.state_repository.s3 import S3StateRepository

# from ttflow.state_repository.dynamodb import DynamoDBStateRepository


@pytest.mark.network
@pytest.mark.parametrize(
    "s",
    [
        S3StateRepository("ttflow-main", prefix="test"),
        # DynamoDBStateRepository("ttflow"),
    ],
)
def test_StateRepository(s):
    s.save_state("ほげ", {"a": 6})
    a = s.read_state("ほげ")
    assert a == {"a": 6}

    a = s.read_state("notfoundkey", default="aaaaaa")
    assert a == "aaaaaa"

    s.unlock_state()
    assert not s.is_locked()
    s.lock_state()
    assert s.is_locked()
    s.unlock_state()
    assert not s.is_locked()
