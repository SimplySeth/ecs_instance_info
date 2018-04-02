#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '2.2',
    'status': ['preview'],
    'supported_by': 'maintainer'
}

DOCUMENTATION = '''
---
module: ecs_instance_info

short_description: Query for vpc,subnets and instance arns for a specified cluster.

version_added: "0.0.1"

description:
    - "A module to query for vpc,subnets and instance arns for a specified cluster."

options:
    aws_access_key:
        description:
            - AWS Access Key
        required: false
    aws_secret_key:
        description:
            - AWS Secret Key
        required: false
    region:
        description:
            - What region you wish to query.
        required: true
    cluster:
        description:
          - What ECS cluster you wish to query.
        required: true
'''

EXAMPLES = '''
- name: With Keys
  ecs_instance_info:
    aws_access_key: "AccessKey"
    aws_secret_key: "SecretKey"
    region: "RegionName"
    cluster: "ClusterName"

- name: Without Keys
  ecs_instance_info:
    region: "RegionName"
    cluster: "ClusterName"
'''

RETURN = '''
avail_zones:
    Description: "List of availability zones."
instances:
    Description: "List of instance arns for the cluster."
subnets:
    Description: "List of subnet ids."
vpc:
    Description: "vpc id."
'''


from ansible.module_utils.basic import AnsibleModule
try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

import pprint
import sys
import json
from collections import OrderedDict

def main():
  # define the available arguments/parameters that a user can pass to
  # the module
  module_args = dict(
      region=dict(type='str',required=True),
      aws_access_key=dict(type='str',required=False,no_log=True),
      aws_secret_key=dict(type='str',required=False,no_log=True),
      aws_session_token=dict(type='str',required=False,no_log=True),
      cluster=dict(type='str',required=True)
  )

  module = AnsibleModule(
    argument_spec=module_args,
    supports_check_mode=False
  )

  result = dict(
      changed=False,
      results=dict()
  )

  if not module.params['region']:
      module.fail_json(msg="Region not specified.")
  if not module.params['cluster']:
      module.fail_json(msg="Cluster not specified.")

  try:
    ecs = boto3.setup_default_session(region_name=module.params['region'])
    if module.params['aws_session_token'] and module.params['aws_access_key'] and module.params['aws_secret_key']:
        ecs = boto3.client('ecs',
            aws_access_key_id=module.params['aws_access_key'],
            aws_secret_access_key=module.params['aws_secret_key'],
            aws_session_token=module.params['aws_session_token'])
    elif module.params['aws_access_key'] and module.params['aws_secret_key']:
        ecs = boto3.client('ecs',
            aws_access_key_id=module.params['aws_access_key'],
            aws_secret_access_key=module.params['aws_secret_key'])
    else:
        ecs = boto3.client('ecs')

    azs = list()
    instances = list()
    results = dict()
    subnets = list()

    attributes = ecs.list_attributes(
        cluster=module.params['cluster'],
        targetType='container-instance',
        attributeName='ecs.vpc-id',
        maxResults=1)
    subnets_data = ecs.list_attributes(
        cluster=module.params['cluster'],
        targetType='container-instance',
        attributeName='ecs.subnet-id')
    azones_data = ecs.list_attributes(
        cluster=module.params['cluster'],
        targetType='container-instance',
        attributeName='ecs.availability-zone')
    instances_data = ecs.list_container_instances(cluster=module.params['cluster'])

    results['vpc'] = attributes['attributes'][0]['value']
    for sb in subnets_data['attributes']:
      subnets.append(sb['value'])
    results['subnets'] = sorted(list(set(subnets)))
    for az in azones_data['attributes']:
      azs.append(az['value'])
    results['avail_zones'] = sorted(list(set(azs)))
    for i in instances_data['containerInstanceArns']:
      instances.append(i)
    results['instances'] = sorted(instances)
    output = OrderedDict(sorted(results.items(), key=lambda t: t[0]))
    result['results'] = output
  except ecs.exceptions.ClusterNotFoundException:
    result['changed'] = False
    module.fail_json(msg="No cluster named: {}".format(module.params['cluster']))
  except Exception as e:
    result['changed'] = False
    module.fail_json(msg=e.message)

  module.exit_json(**result)

if __name__ == '__main__':
    main()
