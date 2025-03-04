import pulumi
import pulumi_aws as aws

size = 't2.micro'
ami = aws.ec2.get_ami(most_recent="true",
                  owners=["137112412989"],
                  filters=[{"name":"name","values":["amzn2-ami-hvm-*"]}])

vpc = aws.ec2.Vpc("webserver-vpc", cidr_block="10.10.0.0/16", enable_dns_hostnames=True, enable_dns_support=True)
route_table = aws.ec2.RouteTable("webserver-rt", vpc_id=vpc.id)
igw = aws.ec2.InternetGateway("webserver-igw", vpc_id=vpc.id)
subnet = aws.ec2.Subnet("webserver-subnet", vpc_id=vpc.id, cidr_block = "10.10.10.0/24", map_public_ip_on_launch=True)
route = aws.ec2.Route("webserver-route", route_table_id=route_table.id, destination_cidr_block="0.0.0.0/0", gateway_id=igw.id)

route_table_association = aws.ec2.RouteTableAssociation(
    "webserver-rta",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

group = aws.ec2.SecurityGroup('webserver-secgrp',vpc_id=vpc.id,
    description='Enable HTTP access',
    ingress=[
        { 'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0'] }
    ])

user_data = """#!/bin/bash
# Install Python 3
sudo yum install -y python3

# Create the index.html file in the /home/ec2-user directory
echo "Hello, World!" > /home/ec2-user/index.html

# Start a simple HTTP server using Python 3 in the /home/ec2-user directory
cd /home/ec2-user
nohup python3 -m http.server 80 &
"""

server = aws.ec2.Instance('webserver-www',
    instance_type=size,
    vpc_security_group_ids=[group.id], # reference security group from above
    opts=pulumi.ResourceOptions(depends_on=[igw]),
    user_data=user_data,
    ami=ami.id,
    subnet_id=subnet.id,
    tags={ "Name": "webserver-www" })

pulumi.export('publicIp', server.public_ip)
pulumi.export('privateIP', server.private_ip)
pulumi.export('publicHostName', server.public_dns)
