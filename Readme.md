## --- Activate the Virtual Environment --- ##
```
Windows:
    .\.venv\Scripts\Activate.ps1
```

```
Linux:
    source ./venv/bin/activate
```
### --- Docker build --- ###
```
docker build -t nhqb3197/nhqb-cloud-kinetics:{$IMAGE_TAG} -f Dockerfile .
```

### --- Docker push --- ###
```
docker push nhqb3197/nhqb-cloud-kinetics:{$IMAGE_TAG}
```

### --- Set up Local Stack --- ###
### Create ECR Repository in LocalStack ###
```powershell
awslocal ecr create-repository `
    --repository-name localstack-ecr-repository `
    --image-scanning-configuration scanOnPush=true
```

### Create stack for ECS Fargate ###
```powershell
awslocal ecs create-cluster --cluster-name reflex-chatbot-cluster
```

### Create DynamoDB Table ###
```powershell
awslocal dynamodb create-table --table-name ChatSession `
>>   --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=session_id,AttributeType=S `
>>   --key-schema AttributeName=user_id,KeyType=HASH AttributeName=session_id,KeyType=RANGE `
>>   --billing-mode PAY_PER_REQUEST 
```

### Tag Docker Image ###
```powershell
docker tag nhqb-cloud-kinetics 000000000000.dkr.ecr.ap-northeast-1.localhost.localstack.cloud:4566/localstack-ecr-repository
```

### Push Docker Image to LocalStack ECR ###
```powershell
docker push 000000000000.dkr.ecr.ap-northeast-1.localhost.localstack.cloud:4566/localstack-ecr-repository
```

### --- Verify Docker Image in LocalStack ECR --- ###
```powershell
awslocal ecr list-images --repository-name localstack-ecr-repository
```
### --- Deploy CloudFormation Stacks --- ###
```powershell
awslocal cloudformation deploy `
    --stack-name reflex-chatbot-cluster `
    --template-file ".\templates\ecs.infra.yaml" `
    --capabilities CAPABILITY_IAM
```

### Deploy ECS Service Stack ###
```powershell
awslocal cloudformation deploy `
    --stack-name reflex-chatbot-service `
    --template-file "./templates/ecs.service.yaml" `
    --capabilities CAPABILITY_IAM `
    --parameter-overrides `
            ContainerImage=000000000000.dkr.ecr.ap-northeast-1.localhost.localstack.cloud:4566/localstack-ecr-repository:latest `
            ExistingClusterName=reflex-chatbot-cluster `
            ServiceName=reflex-chatbot-service
```