import json

from aws.s3 import AWSS3


def test_save_dict_to_json(s3_client, s3_create_bucket):
    awss3 = AWSS3(aws_access_key_id="testing", aws_secret_access_key="testing", bucket_name="test_bucket")
    awss3.client = s3_client

    test_dict = {"key": "value"}
    awss3.save_dict_to_json(test_dict, "test.json")

    response = s3_client.get_object(Bucket="test_bucket", Key="test.json")
    data = json.loads(response["Body"].read().decode())

    assert data == test_dict


def test_list_files_from_path(s3_client, s3_create_bucket):
    awss3 = AWSS3(aws_access_key_id="testing", aws_secret_access_key="testing", bucket_name="test_bucket")
    awss3.client = s3_client

    s3_client.put_object(Bucket="test_bucket", Key="test.json", Body=json.dumps({"key": "value"}))

    assert awss3.list_files_from_path() == ["test.json"]


def test_read_json(s3_client, s3_create_bucket):
    awss3 = AWSS3(aws_access_key_id="testing", aws_secret_access_key="testing", bucket_name="test_bucket")
    awss3.client = s3_client

    test_dict = {"key": "value"}
    s3_client.put_object(Bucket="test_bucket", Key="test.json", Body=json.dumps(test_dict))

    assert awss3.read_json("test.json") == test_dict
