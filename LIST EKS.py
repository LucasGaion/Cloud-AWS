import boto3
from openpyxl import Workbook
from datetime import date, datetime

def crossAccountAssumeRole(stsClient, setupAccountId, environment):
    response = stsClient.assume_role(
        RoleArn='arn:aws:iam::' + setupAccountId + ':role/OrganizationAccountAccessRole',
        RoleSessionName='session' + setupAccountId
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
    accountId = []
    accountName = []
    for page in iterator:
        for userAccount in page['Accounts']:
            if '174497301150' not in userAccount['Id'] \
                    and '805247736219' not in userAccount['Id'] \
                    and '155168398419' not in userAccount['Id'] \
                    and '198692157349' not in userAccount['Id'] \
                    and '711833812546' not in userAccount['Id'] \
                    and '949385213276' not in userAccount['Id']:
                accountId.append({'Account': userAccount['Id'], 'Name': userAccount['Name']})
    return accountId

regions = ['us-east-1', 'sa-east-1']

orgClient = boto3.client('organizations')
accounts = getSetupAccount(orgClient)

workbook = Workbook()
worksheet = workbook.active

worksheet.append([
    'Contas',
    'Região',
    'name'
])

stsClient = boto3.client('sts')

for contas in accounts:
    credentials = crossAccountAssumeRole(stsClient, contas['Account'], 'dev')

    for region in regions:
        try:
            print(f"{contas['Name']} - {region}")

            eks_client = credentials.client('eks', region_name=region)
            cluster = eks_client.describe_cluster()

            for eks in cluster['cluster']:
                    worksheet.append([
                        contas['Name'],
                        region,
                        eks('name'),
                    ])

        except BaseException as e:
            print('ERRO:', str(e))

data = date.today()
sheetWATCH = f'LIST NAT GATEWAYS - {data}.xlsx'
workbook.save(filename=sheetWATCH)
print(f'Salvo com sucesso: {sheetWATCH}')
