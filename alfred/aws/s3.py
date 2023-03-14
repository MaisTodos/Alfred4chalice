import base64
import uuid

import boto3
from botocore.exceptions import ClientError

from alfred.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_S3
from botocore.config import Config


s3_client = boto3.client(
    "s3",
    config=Config(signature_version='s3v4'),
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


class S3File:
    EXTENSIONS = {
        "image/png": "png",
        "image/jpg": "jpg",
        "image/jpeg": "jpg",
    }

    @classmethod
    def _random_file_name(cls, data):
        name = str(uuid.uuid4())

        extension_start = data.find(":") + 1
        extension_end = data.find(";")
        extension_key = data[extension_start:extension_end]
        extension = cls.EXTENSIONS[extension_key]

        return f"{name}.{extension}"

    @classmethod
    def upload_file(cls, base64_file, upload_to, file_name=None, bucket=BUCKET_S3):
        """
        Esse método recebe um base64 e sobe para o S3 retornando uma url assinada.

        :param data: base64 do arquivo.
        """
        # Dividir o data do base64
        # Ex: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAu4AAA....IIA==
        base64_splited = base64_file.split(",")

        try:
            base64_data = base64_splited[1]
        except IndexError as err:
            return False, f"IndexError: {str(err)}"

        try:
            body = base64.b64decode(base64_data)
        except base64.binascii.Error as err:
            return False, f"Base64Error: {str(err)}"

        if not file_name:
            file_name = cls._random_file_name(base64_splited[0])
        path = f"{upload_to}/{file_name}"

        try:
            s3_client.put_object(Body=body, Bucket=bucket, Key=path)
        except ClientError as err:
            return False, f"S3ClientError: {str(err)}"

        return True, path

    @classmethod
    def get_presigned_url(cls, path, bucket=BUCKET_S3):
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": path}
        )
        return url
