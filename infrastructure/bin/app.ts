#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SocraticBenchmarksStack } from '../lib/socratic-bench-stack';

const app = new cdk.App();

new SocraticBenchmarksStack(app, 'SocraticBenchmarksStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'Socratic AI Benchmarks - DynamoDB + S3 + Lambda Data Layer',
});

app.synth();
