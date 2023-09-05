import os

import boto3
import pytest
from moto import mock_s3


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def s3_client(aws_credentials):
    with mock_s3():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def s3_create_bucket(s3_client):
    s3_client.create_bucket(Bucket="test_bucket")
