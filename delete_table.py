import boto3

client = boto3.client('dynamodb',
                      aws_access_key_id="fakeMyKeyId",
                      aws_secret_access_key="fakeSecretAccessKey",
                      region_name='us-east-1',
                      endpoint_url='http://localhost:8000')



try:
    resp = client.delete_table(
        TableName="Events",
    )
    print("Table deleted successfully!")
except Exception as e:
    print("Error deleting table:")
    print(e)
