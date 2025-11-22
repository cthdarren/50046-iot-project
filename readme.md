# 50.046 Cloud Computing and IoT - Final Project

## Project Description

Our goal is to create an analytics system for restrooms in places with high traffic (e.g. Shopping malls and institutions).

The main features of our project:

- Display of restroom unit occupancy to surrounding people, increasing convenience and improving the experience of urgent restroom users.
- Analysis of restroom usage to encourage efficient cleaning and maintenance deployments.

To execute this we have come up with the following solution.

## System Diagram

![system design image](assets/images/cloud_and_iot_sys_diagram.png)

## Running the Project

### Production Deployment

Ensure you have `aws-cli` and `terraform` installed locally on your machine.

To deploy, we first have to create the RDS credentials in AWS SecretsManager. Note that these secrets will be used for the production deployment so please change the username and password to secure ones. Use `aws-cli` to create the secret by running:

```bash
aws secretsmanager create-secret \
  --name rds_credentials \
  --secret-string '{"username":"iot_master","password":"S3cureRandomPassw0rd!"}'
```

After creating the secrets, use terraform to apply the infrastructure under your AWS account.

```bash
terraform apply
```

### Running Locally

_TODO_
