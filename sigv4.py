import hashlib

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def sign(method, url, body, host, headers, service="s3tables", region="local", access_key=None, secret_key=None):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    headers['x-amz-content-sha256'] = payload_hash
    headers['Host'] = host.replace("http://", "").replace("https://", "")

    request = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers=headers,
    )
    SigV4Auth(session.get_credentials(), service, region).add_auth(request)
    return request


def main():
    # Example configuration
    access_key = "minioadmin"
    secret_key = "minioadmin"
    host = "localhost:9000"
    method = "GET"
    url = f"http://{host}/"
    body = ""
    service = "s3"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Sign the request
    signed_request = sign(
        method=method,
        url=url,
        body=body,
        service=service,
        host=host,
        headers=headers,
        access_key=access_key,
        secret_key=secret_key
    )

    # Display the signed request details
    print("Signed Request Details:")
    print(f"Method: {signed_request.method}")
    print(f"URL: {signed_request.url}")
    print("\nHeaders:")
    for key, value in signed_request.headers.items():
        print(f"  {key}: {value}")

    # Generate curl command
    print("\n" + "="*60)
    print("Curl command:")
    print("="*60)
    curl_cmd = f"curl -X {signed_request.method}"
    for key, value in signed_request.headers.items():
        curl_cmd += f" \\\n  -H '{key}: {value}'"
    if body:
        curl_cmd += f" \\\n  -d '{body}'"
    curl_cmd += f" \\\n  '{signed_request.url}'"
    print(curl_cmd)


if __name__ == "__main__":
    main()