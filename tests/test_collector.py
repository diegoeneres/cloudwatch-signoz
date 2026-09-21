from datetime import datetime, timezone

from cloudwatch_signoz.aws import AwsTargetClient, Instance, Sample
from cloudwatch_signoz.config import Target
from cloudwatch_signoz.signoz import otlp_payload


class Paginator:
    def paginate(self, **kwargs):
        return [{"Reservations": [{"Instances": [
            {"InstanceId": "i-t", "InstanceType": "t3.micro", "Tags": [{"Key": "Name", "Value": "api"}]},
            {"InstanceId": "i-m", "InstanceType": "m6i.large"},
        ]}]}]


class EC2:
    def get_paginator(self, name):
        assert name == "describe_instances"
        return Paginator()


class CloudWatch:
    def get_metric_data(self, **kwargs):
        assert kwargs["MetricDataQueries"][0]["MetricStat"]["Period"] == 300
        return {"MetricDataResults": [{
            "Id": "m0", "Values": [42.0], "Timestamps": [datetime(2026, 1, 1, tzinfo=timezone.utc)]
        }]}


class Session:
    def client(self, service, **kwargs):
        return EC2() if service == "ec2" else CloudWatch()


def test_discovers_only_t_family_and_collects_latest_value():
    client = AwsTargetClient(Target("123", "sa-east-1"), Session())
    instances = client.discover_instances()
    assert instances == [Instance("i-t", "t3.micro", "api")]
    sample = client.collect(instances, 600)[0]
    assert sample.value == 42.0
    assert sample.account == "123"


def test_otlp_payload_has_filters_required_by_proposal():
    sample = Sample(
        "123", "sa-east-1", Instance("i-1", "t4g.small", "worker"), 10.5,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    payload = otlp_payload([sample])
    metric = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]
    assert metric["name"] == "aws.ec2.cpu_credit_balance"
    attrs = metric["gauge"]["dataPoints"][0]["attributes"]
    assert {a["key"] for a in attrs} >= {"cloud.account.id", "cloud.region", "host.id", "host.name"}

