import sys
import boto3
import argparse

def create_presigned_url(bucket_name, object_key, expiration=3600):
    """Generate a presigned URL for an S3 object."""
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_key},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a presigned URL for an S3 object.')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--key', required=True, help='S3 object key')
    args = parser.parse_args()

    url = create_presigned_url(args.bucket, args.key)
    if url:
        print(url)
