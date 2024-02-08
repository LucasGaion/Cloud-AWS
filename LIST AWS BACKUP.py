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
            if userAccount['Id'] not in ['174497301150', '805247736219', '155168398419', '198692157349', '711833812546', '949385213276']:
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
    'BackupPlanName',
    'BackupPlanId',
    'BackupPlanArn',
])

stsClient = boto3.client('sts')

for contas in accounts:
    credentials = crossAccountAssumeRole(stsClient, contas['Account'], 'Name')

    for region in regions:
        try:
            print(f"{contas['Name']} - {region}")

            backup_client = credentials.client('backup', region_name=region)
            aws = backup_client.list_backup_plans()

            for backup in aws['BackupPlansList']:
                worksheet.append([
                    contas['Name'],
                    region,
                    backup['BackupPlanName'],
                    backup['BackupPlanId'],
                    backup['BackupPlanArn'],
                ])

        except Exception as e:
            print('ERRO:', str(e))

data = date.today()
sheetBACKUP = f'LIST AWS BACKUP - {data}.xlsx'
workbook.save(filename=sheetBACKUP)
print(f'Salvo com sucesso: {sheetBACKUP}')
