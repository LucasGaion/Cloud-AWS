import boto3
from openpyxl import Workbook
from datetime import date


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
    'AcceleratorArn',
    'Name',
    'IpAddressType',
])

stsClient = boto3.client('sts')

for contas in accounts:
    credentials = crossAccountAssumeRole(stsClient, contas['Account'], 'Name')

    for region in regions:
        try:

            print(f"{contas['Name']} - {region}")

            globalaccelerator = credentials.client('globalaccelerator', region_name=region)
            globals = globalaccelerator.list_accelerators()

            for accelarator in globals['Accelerators']:
                worksheet.append([
                    contas['Name'],
                    region,
                    accelarator['AcceleratorArn'],
                    accelarator['Name'],
                    accelarator['IpAddressType'],
                ])

        except BaseException as e:
            print('ERRO:', str(e))

data = date.today()
sheetGLOBAL = f'LIST GLOBAL ACCELARATOR - {data}.xlsx'
workbook.save(filename=sheetGLOBAL)
print(f'Salvo com sucesso: {sheetGLOBAL}')



