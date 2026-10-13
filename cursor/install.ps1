$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $env:USERPROFILE ".cursor\plugins\local\benchmark-agent"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Path (Join-Path $source "*") -Destination $dest -Recurse -Force
Write-Host "已安装到 $dest"
Write-Host "重新打开 Cursor 后，在设置的插件列表中确认“模型评测”。"
