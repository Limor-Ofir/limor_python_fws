import argparse
import boto3
import sys

# Initialize the AWS clients
ec2 = boto3.client('ec2')
s3 = boto3.client('s3')
route53 = boto3.client('route53')

def main():
    parser = argparse.ArgumentParser(description='AWS Resource Provisioning CLI')
    subparsers = parser.add_subparsers(dest='resource_type')

    # EC2 parser
    ec2_parser = subparsers.add_parser('ec2', help='Manage EC2 instances')
    ec2_subparsers = ec2_parser.add_subparsers(dest='action')
    
    ec2_create_parser = ec2_subparsers.add_parser('create', help='Create EC2 instance')
    ec2_create_parser.add_argument('--instance-type', choices=['t3.nano', 't4g.nano'], required=True, help='Type of EC2 instance')
    ec2_create_parser.add_argument('--ami', choices=['ubuntu', 'amazon-linux'], required=True, help='AMI choice')
    
    ec2_manage_parser = ec2_subparsers.add_parser('manage', help='Manage EC2 instances')
    ec2_manage_parser.add_argument('--instance-id', required=True, help='ID of the EC2 instance')
    ec2_manage_parser.add_argument('--action', choices=['start', 'stop'], required=True, help='Action to perform on the instance')

    ec2_list_parser = ec2_subparsers.add_parser('list', help='List EC2 instances')

    # S3 parser
    s3_parser = subparsers.add_parser('s3', help='Manage S3 buckets')
    s3_subparsers = s3_parser.add_subparsers(dest='action')
    
    s3_create_parser = s3_subparsers.add_parser('create', help='Create S3 bucket')
    s3_create_parser.add_argument('--bucket-name', required=True, help='Name of the S3 bucket')
    s3_create_parser.add_argument('--public', action='store_true', help='Public access')

    s3_upload_parser = s3_subparsers.add_parser('upload', help='Upload file to S3 bucket')
    s3_upload_parser.add_argument('--bucket-name', required=True, help='Name of the S3 bucket')
    s3_upload_parser.add_argument('--file', required=True, help='Path to the file')

    s3_list_parser = s3_subparsers.add_parser('list', help='List S3 buckets')

    # Route53 parser
    route53_parser = subparsers.add_parser('route53', help='Manage Route53 DNS records')
    route53_subparsers = route53_parser.add_subparsers(dest='action')
    
    route53_create_parser = route53_subparsers.add_parser('create', help='Create DNS zone')
    route53_create_parser.add_argument('--zone-name', required=True, help='Name of the DNS zone')

    route53_manage_parser = route53_subparsers.add_parser('manage', help='Manage DNS records')
    route53_manage_parser.add_argument('--zone-id', required=True, help='ID of the DNS zone')
    route53_manage_parser.add_argument('--record', required=True, help='DNS record details')

    args = parser.parse_args()
    # Handle each command
    if args.resource_type == 'ec2':
        handle_ec2_commands(args)
    elif args.resource_type == 's3':
        handle_s3_commands(args)
    elif args.resource_type == 'route53':
        handle_route53_commands(args)
    else:
        parser.print_help()

def handle_ec2_commands(args):
    if args.action == 'create':
        instances = ec2.describe_instances(Filters=[{'Name': 'tag:CreatedByCLI', 'Values': ['true']}])
        running_instances = [i for r in instances['Reservations'] for i in r['Instances'] if i['State']['Name'] == 'running']
        
        if len(running_instances) >= 2:
            print("Error: Cannot create more than 2 running instances.")
            return
        
        if args.ami == 'ubuntu':
            ami_id = 'ami-12345678'  # Replace with actual latest Ubuntu AMI ID
        elif args.ami == 'amazon-linux':
            ami_id = 'ami-87654321'  # Replace with actual latest Amazon Linux AMI ID
       
        instance = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=args.instance_type,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'CreatedByCLI', 'Value': 'true'}]
            }]
        )
        print(f"Created instance {instance['Instances'][0]['InstanceId']}")
    
    elif args.action == 'manage':
        instance_id = args.instance_id
        if args.action == 'start':
            ec2.start_instances(InstanceIds=[instance_id])
            print(f"Started instance {instance_id}")
        elif args.action == 'stop':
            ec2.stop_instances(InstanceIds=[instance_id])
            print(f"Stopped instance {instance_id}")

    elif args.action == 'list':
        instances = ec2.describe_instances(Filters=[{'Name': 'tag:CreatedByCLI', 'Values': ['true']}])
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                print(f"Instance ID: {instance['InstanceId']}, State: {instance['State']['Name']}")

def handle_s3_commands(args):
    if args.action == 'create':
        if args.public:
            confirm = input("Are you sure you want to create a public bucket? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Bucket creation cancelled.")
                return

        s3.create_bucket(Bucket=args.bucket_name, CreateBucketConfiguration={
            'LocationConstraint': 'us-west-2'})  # Change region if needed

        if args.public:
            s3.put_bucket_acl(Bucket=args.bucket_name, ACL='public-read')
        
        print(f"Created bucket {args.bucket_name}")

    elif args.action == 'upload':
        buckets = s3.list_buckets()
        if args.bucket_name not in [b['Name'] for b in buckets['Buckets']]:
            print(f"Bucket {args.bucket_name} does not exist or was not created via this CLI.")
            return

        with open(args.file, 'rb') as file_data:
            s3.upload_fileobj(file_data, args.bucket_name, args.file)
        print(f"Uploaded {args.file} to bucket {args.bucket_name}")

    elif args.action == 'list':
        buckets = s3.list_buckets()
        for bucket in buckets['Buckets']:
            print(f"Bucket Name: {bucket['Name']}")

def handle_route53_commands(args):
    if args.action == 'create':
        response = route53.create_hosted_zone(Name=args.zone_name, CallerReference=str(hash(args.zone_name)))
        print(f"Created DNS zone {args.zone_name}, ID: {response['HostedZone']['Id']}")

    elif args.action == 'manage':
        # Add logic for managing DNS records here
        pass

if __name__ == '__main__':
    main()
