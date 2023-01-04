from ttflow.state_repository.dynamodb import DynamoDBStateRepository


def test_dynamodbのテスト():
    s = DynamoDBStateRepository("ttflow")
    s.save_state("ほげ", {"a": 6})
    a = s.read_state("ほげ")
    assert a == {"a": 6}
