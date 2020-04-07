import boto3

# boto3 is the AWS SDK library for Python.
# We can use the low-level client to make API calls to DynamoDB.
client = boto3.client('dynamodb',
                      aws_access_key_id="fakeMyKeyId",
                      aws_secret_access_key="fakeSecretAccessKey",
                      region_name='us-east-1',
                      endpoint_url='http://localhost:8000')

try:
    resp = client.create_table(
        TableName="Events",
        # Declare your Primary Key in the KeySchema argument
        KeySchema=[
            {
                "AttributeName": "Date",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "Name",
                "KeyType": "RANGE"
            }
        ],
        # Any attributes used in KeySchema or Indexes must be declared in AttributeDefinitions
        AttributeDefinitions=[
            {
                "AttributeName": "Date",
                "AttributeType": "S"
            },
            {
                "AttributeName": "Name",
                "AttributeType": "S"
            }
        ],
        # ProvisionedThroughput controls the amount of data you can read or write to DynamoDB per second.
        # You can control read and write capacity independently.
        ProvisionedThroughput={
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1
        }
    )
    print("Table created successfully!")
except Exception as e:
    print("Error creating table:")
    print(e)
