# 测试文件上传到混凝土表格识别技能
# 使用方法: .\test_file_upload.ps1 -FilePath "C:\path\to\your\file.pdf"

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [string]$Format = "json",
    [string]$OutputDir = "",
    [string]$ApiUrl = "http://localhost:8000"
)

# 检查文件是否存在
if (-not (Test-Path $FilePath)) {
    Write-Host "❌ 错误: 文件不存在: $FilePath" -ForegroundColor Red
    exit 1
}

Write-Host "📁 准备上传文件: $FilePath" -ForegroundColor Cyan
Write-Host "📋 格式: $Format" -ForegroundColor Cyan

# 构建表单数据
$form = @{
    file = Get-Item $FilePath
    format = $Format
}

if ($OutputDir) {
    $form["output_dir"] = $OutputDir
}

try {
    Write-Host "`n🚀 正在上传并处理文件..." -ForegroundColor Yellow
    
    $response = Invoke-RestMethod -Uri "$ApiUrl/api/skill/concrete-table-recognition" `
        -Method Post `
        -Form $form `
        -ErrorAction Stop
    
    Write-Host "`n✅ 处理成功！" -ForegroundColor Green
    Write-Host "`n📊 结果:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
    
    # 保存结果到文件
    $outputFile = "result_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $response | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputFile -Encoding UTF8
    Write-Host "`n💾 结果已保存到: $outputFile" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "详细信息: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}
