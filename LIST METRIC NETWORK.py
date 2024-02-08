import boto3
from datetime import datetime, timedelta, date
from openpyxl import Workbook

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
                    and '711833812546' not in userAccount ['Id'] \
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
    'InstanceId',
    'NetworkOutBytes',
    'NetworkInBytes'
])

stsClient = boto3.client('sts')

for contas in accounts:
    credentials = crossAccountAssumeRole(stsClient, contas['Account'], 'dev')

    for region in regions:
        try:
            print(f"{contas['Name']} - {region}")

            ec2_client = credentials.client('ec2', region_name=region)
            instances = ec2_client.describe_instances()

            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']

                    cloudwatch_client = credentials.client('cloudwatch', region_name=region)
                    network_out_metric = cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='NetworkOut',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=datetime.utcnow() - timedelta(minutes=5),
                        EndTime=datetime.utcnow(),
                        Period=300,
                        Statistics=['Average'],
                        Unit='Bytes'
                    )
                    network_in_metric = cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='NetworkIn',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=datetime.utcnow() - timedelta(minutes=5),
                        EndTime=datetime.utcnow(),
                        Period=300,
                        Statistics=['Average'],
                        Unit='Bytes'
                    )

                    network_out_value = "{:,.1f}".format(network_out_metric['Datapoints'][0]['Average']) if network_out_metric['Datapoints'] else None
                    network_in_value = "{:,.1f}".format(network_in_metric['Datapoints'][0]['Average']) if network_in_metric['Datapoints'] else None

                    worksheet.append([
                        contas['Name'],
                        region,
                        instance_id,
                        network_out_value,
                        network_in_value
                    ])

        except BaseException as e:
            print('ERRO:', str(e))

data = date.today()
sheetMETRIC = f'LIST METRIC NETWORK (AWS) - {data}.xlsx'
workbook.save(filename=sheetMETRIC)
print(f'Salvo com sucesso: {sheetMETRIC}')
