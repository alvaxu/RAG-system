# 定义原始文件名和新文件名的映射
$files = @{
    "5.0.0_feature_engineering.py" = "v500_feature_engineering.py"
    "5.0.0_kline_plot.py"          = "v500_kline_plot.py"
    "5.0.0_boll_detection.py"      = "v500_boll_detection.py"
    "5.0.0_arima_stock.py"         = "v500_arima_stock.py"
    "5.0.0_prophet_analysis.py"    = "v500_prophet_analysis.py"
    "5.0.0_prophet_predict.py"     = "v500_prophet_predict.py"
    "5.0.0_lstm_predict.py"        = "v500_lstm_predict.py"
}

# 1. 重命名文件
foreach ($old in $files.Keys) {
    $new = $files[$old]
    if (Test-Path $old) {
        Rename-Item $old $new
        Write-Host "已重命名 $old -> $new"
    }
}

# 2. 批量替换import语句
# 只处理当前目录下的py文件
$pyFiles = Get-ChildItem -Path . -Filter *.py

foreach ($pyFile in $pyFiles) {
    $content = Get-Content $pyFile.FullName -Raw
    foreach ($old in $files.Keys) {
        $oldMod = [System.IO.Path]::GetFileNameWithoutExtension($old)
        $newMod = [System.IO.Path]::GetFileNameWithoutExtension($files[$old])
        # 替换 from ... import ... 和 import ... 两种形式
        $content = $content -replace "from\s+$oldMod\s+import", "from $newMod import"
        $content = $content -replace "import\s+$oldMod", "import $newMod"
    }
    Set-Content $pyFile.FullName $content
    Write-Host "已更新import: $($pyFile.Name)"
}
