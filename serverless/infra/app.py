#!/usr/bin/env python3
"""
AWS CDK app for Socratic AI Benchmarks serverless infrastructure.
"""

import aws_cdk as cdk
from stack import SocraticBenchStack

app = cdk.App()

SocraticBenchStack(
    app,
    "SocraticBenchStack",
    description="Serverless Socratic AI Benchmarking Platform",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1",
    ),
)

app.synth()
