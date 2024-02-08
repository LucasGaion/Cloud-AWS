import boto3
from openpyxl import Workbook
from datetime import date

def crossAccountAssumeRole(stsClient, setupAccountId, environment):
    response = stsClient.assume_role(
        RoleArn=f'arn:aws:iam::{setupAccountId}:role/OrganizationAccountAccessRole',
        RoleSessionName=f'session{setupAccountId}'
    )
    session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken']
    )
    return session

def getSetupAccount(orgClient):
    paginator = orgClient.get_paginator('list_accounts')
    iterator = paginator.paginate()
    accounts = []

    for page in iterator:
        for userAccount in page['Accounts']:
            if userAccount['Id'] not in ['174497301150', '805247736219', '155168398419', '198692157349', '711833812546', '949385213276']:
                accounts.append({'Account': userAccount['Id'], 'Name': userAccount['Name']})

    return accounts

regions = ['us-east-1', 'sa-east-1']

orgClient = boto3.client('organizations')
accounts = getSetupAccount(orgClient)

workbook = Workbook()
worksheet = workbook.active

worksheet.append([
    'Contas',
    'Região',
    'VpcEndpointId',
    'ServiceName'
])

stsClient = boto3.client('sts')

for account in accounts:
    credentials = crossAccountAssumeRole(stsClient, account['Account'], 'dev')

    for region in regions:
        try:
            print(f"{account['Name']} - {region}")

            vpc_client = credentials.client('ec2', region_name=region)
            endpoints = vpc_client.describe_vpc_endpoints()

            for endpoint in endpoints['VpcEndpoints']:
                worksheet.append([
                    account['Name'],
                    region,
                    endpoint['VpcEndpointId'],
                    endpoint['ServiceName'],
                ])

        except Exception as e:
            print('ERRO:', str(e))

data = date.today()
sheetVPC = f'LIST VPC ENDPOINTS - {data}.xlsx'
workbook.save(filename=sheetVPC)
print(f'Salvo com sucesso: {sheetVPC}')
