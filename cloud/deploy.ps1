param(
    [string]$StackName = "SmartSiteGuardStack",
    [string]$Region = "us-east-1"
)

Set-Location -Path $PSScriptRoot

Write-Host "Deploying CloudFormation stack $StackName in region $Region..."
aws cloudformation deploy --template-file template.yaml --stack-name $StackName --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment completed successfully."
} else {
    Write-Error "Deployment failed with exit code $LASTEXITCODE."
}
