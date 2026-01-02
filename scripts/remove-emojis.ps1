# Remove Emojis from Markdown Files
# This script removes emoji characters from all markdown files in the docs directory

$docsPath = "C:\Users\lu\Downloads\Proyectos\Infraestructuras\infra-paralela-common-crawl-colcap\docs"
$mdFiles = Get-ChildItem -Path $docsPath -Filter "*.md" -Recurse

foreach ($file in $mdFiles) {
    Write-Host "Processing: $($file.FullName)"
    
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    
    # Remove emojis using regex (Unicode emoji ranges)
    $cleaned = $content -replace '[\x{1F300}-\x{1F9FF}]', ''
    $cleaned = $cleaned -replace '[\x{2600}-\x{26FF}]', ''
    $cleaned = $cleaned -replace '[\x{2700}-\x{27BF}]', ''
    $cleaned = $cleaned -replace '[\x{1F600}-\x{1F64F}]', ''
    $cleaned = $cleaned -replace '[\x{1F680}-\x{1F6FF}]', ''
    $cleaned = $cleaned -replace '[\x{1F1E0}-\x{1F1FF}]', ''
    
    # Remove specific emojis found in files
    $cleaned = $cleaned -replace '[🏗️📦☁️🎯📂✅🔨📤📋🎉🌐📡📚📊🔐📰]', ''
    
    # Clean up extra spaces
    $cleaned = $cleaned -replace '  +', ' '
    $cleaned = $cleaned -replace '# \s+', '# '
    
    Set-Content -Path $file.FullName -Value $cleaned -Encoding UTF8 -NoNewline
    
    Write-Host "Cleaned: $($file.Name)"
}

Write-Host "Emoji removal complete!"
