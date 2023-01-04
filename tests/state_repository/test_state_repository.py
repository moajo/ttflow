import pytest

from ttflow.state_repository.s3 import S3StateRepository
from ttflow.state_repository.dynamodb import DynamoDBStateRepository


@pytest.mark.network
@pytest.mark.parametrize(
    "s",
    [
        S3StateRepository("ttflow-main"),
        DynamoDBStateRepository("ttflow"),
    ],
)
def test_StateRepository(s):
    s.save_state("ほげ", {"a": 6})
    a = s.read_state("ほげ")
    assert a == {"a": 6}

    a = s.read_state("notfoundkey", default="aaaaaa")
    assert a == "aaaaaa"
