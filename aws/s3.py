import json
import os
from dataclasses import dataclass

import boto3
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AWSS3:
    aws_access_key_id: str = os.environ["MINIO_ROOT_USER"]
    aws_secret_access_key: str = os.environ["MINIO_ROOT_PASSWORD"]
    bucket_name: str = os.environ["MINIO_DEFAULT_BUCKET"]

    def __post_init__(self):
        self.__connect_aws_s3()

    def __connect_aws_s3(self):
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        self.client = session.client("s3", endpoint_url="http://localhost:9000")

    def save_dict_to_json(self, item: dict, path: str):
        self.client.put_object(
            Bucket=self.bucket_name,
            Body=json.dumps(item),
            Key=path,
        )

    def list_files_from_path(self, path: str = ""):
        objects = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=path,
        ).get("Contents")

        return [obj.get("Key") for obj in objects] if objects else None

    def read_json(self, path: str) -> dict:
        file_obj = self.client.get_object(Bucket=self.bucket_name, Key=path)
        file_content = file_obj["Body"].read()
        string_content = file_content.decode("utf-8")
        return json.loads(string_content)
