param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,

    [string]$Format = "json",
    [string]$OutputDir = "",
    [string]$ApiUrl = "http://localhost:8000"
)

if (-not (Test-Path $FilePath)) {
    Write-Host "Error: file not found: $FilePath" -ForegroundColor Red
    exit 1
}

$endpoint = "$ApiUrl/api/skill/concrete-table-recognition"
Write-Host "Uploading file: $FilePath" -ForegroundColor Cyan
Write-Host "Endpoint: $endpoint" -ForegroundColor Cyan

$curlArgs = @(
    "-sS",
    "-X", "POST",
    $endpoint,
    "-F", "file=@$FilePath",
    "-F", "format=$Format"
)

if ($OutputDir) {
    $curlArgs += @("-F", "output_dir=$OutputDir")
}

try {
    $raw = & curl.exe @curlArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: curl exited with code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }

    $obj = $raw | ConvertFrom-Json
    $pretty = $obj | ConvertTo-Json -Depth 20

    Write-Host "Request finished." -ForegroundColor Green
    Write-Host $pretty

    $outputFile = "result_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $pretty | Out-File -FilePath $outputFile -Encoding utf8
    Write-Host "Saved response to: $outputFile" -ForegroundColor Green
}
catch {
    Write-Host "Request failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($raw) {
        Write-Host "Raw response:" -ForegroundColor Yellow
        Write-Host $raw
    }
    exit 1
}
