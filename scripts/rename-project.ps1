<#
.SYNOPSIS
    Rename project from one name to another throughout the codebase.
    
.DESCRIPTION
    This script performs a comprehensive rename of a Python project:
    - Renames the main package folder
    - Updates all Python imports
    - Updates pyproject.toml
    - Updates documentation files
    - Updates config paths and environment variables
    
.PARAMETER OldName
    The current project name (e.g., "nanobot")
    
.PARAMETER NewName
    The new project name (e.g., "icron")
    
.PARAMETER ProjectPath
    Path to the project root. Defaults to current directory.
    
.PARAMETER DryRun
    Preview changes without making them.
    
.EXAMPLE
    .\rename-project.ps1 -OldName "nanobot" -NewName "icron"
    
.EXAMPLE
    .\rename-project.ps1 -OldName "nanobot" -NewName "myproject" -DryRun
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$OldName,
    
    [Parameter(Mandatory=$true)]
    [string]$NewName,
    
    [string]$ProjectPath = ".",
    
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Resolve full path
$ProjectPath = Resolve-Path $ProjectPath

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Project Rename Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  From: $OldName" -ForegroundColor Yellow
Write-Host "  To:   $NewName" -ForegroundColor Green
Write-Host "  Path: $ProjectPath" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "  Mode: DRY RUN (no changes will be made)" -ForegroundColor Magenta
}
Write-Host "========================================`n" -ForegroundColor Cyan

# Uppercase versions for env vars
$OldNameUpper = $OldName.ToUpper()
$NewNameUpper = $NewName.ToUpper()

# Function to replace content in a file
function Update-FileContent {
    param(
        [string]$FilePath,
        [hashtable]$Replacements
    )
    
    if (-not (Test-Path $FilePath)) {
        return $false
    }
    
    $content = Get-Content $FilePath -Raw
    $originalContent = $content
    
    foreach ($old in $Replacements.Keys) {
        $new = $Replacements[$old]
        $content = $content -replace [regex]::Escape($old), $new
    }
    
    if ($content -ne $originalContent) {
        if (-not $DryRun) {
            Set-Content -Path $FilePath -Value $content -NoNewline
        }
        return $true
    }
    return $false
}

# Function to process files recursively
function Update-FilesInDirectory {
    param(
        [string]$Directory,
        [string[]]$Extensions,
        [hashtable]$Replacements
    )
    
    $changedCount = 0
    
    Get-ChildItem -Path $Directory -Recurse -File | Where-Object {
        $_.Extension -in $Extensions -and
        $_.FullName -notmatch "\\\.git\\" -and
        $_.FullName -notmatch "\\node_modules\\" -and
        $_.FullName -notmatch "\\__pycache__\\" -and
        $_.FullName -notmatch "\\\.egg-info\\"
    } | ForEach-Object {
        $relativePath = $_.FullName.Replace($ProjectPath, "").TrimStart("\")
        if (Update-FileContent -FilePath $_.FullName -Replacements $Replacements) {
            Write-Host "  [Updated] $relativePath" -ForegroundColor Green
            $changedCount++
        }
    }
    
    return $changedCount
}

# Step 1: Rename package folder
Write-Host "Step 1: Renaming package folder..." -ForegroundColor Yellow
$oldFolder = Join-Path $ProjectPath $OldName
$newFolder = Join-Path $ProjectPath $NewName

if (Test-Path $oldFolder) {
    if (Test-Path $newFolder) {
        Write-Host "  [Warning] Target folder already exists: $NewName" -ForegroundColor Yellow
    } else {
        if (-not $DryRun) {
            Move-Item -Path $oldFolder -Destination $newFolder
        }
        Write-Host "  [Renamed] $OldName/ -> $NewName/" -ForegroundColor Green
    }
} else {
    Write-Host "  [Skip] Folder '$OldName' not found (may already be renamed)" -ForegroundColor Gray
}

# Step 2: Update Python files
Write-Host "`nStep 2: Updating Python imports and references..." -ForegroundColor Yellow

$pythonReplacements = @{
    "from $OldName." = "from $NewName."
    "import $OldName" = "import $NewName"
    ".$OldName/" = ".$NewName/"
    ".$OldName\`"" = ".$NewName`""
    "~/$OldName" = "~/$NewName"
    "~\.$OldName" = "~\.$NewName"
    "${OldNameUpper}_" = "${NewNameUpper}_"
    "`"$OldName`"" = "`"$NewName`""
    "'$OldName'" = "'$NewName'"
    "$OldName - " = "$NewName - "
    "$OldName v" = "$NewName v"
    "# $OldName" = "# $NewName"
    "for $OldName" = "for $NewName"
    "of $OldName" = "of $NewName"
    "is $OldName" = "is $NewName"
    "I am $OldName" = "I am $NewName"
}

$pyCount = Update-FilesInDirectory -Directory $ProjectPath -Extensions @(".py") -Replacements $pythonReplacements
Write-Host "  [Done] Updated $pyCount Python files" -ForegroundColor Cyan

# Step 3: Update configuration files
Write-Host "`nStep 3: Updating configuration files..." -ForegroundColor Yellow

$configFiles = @(
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Dockerfile",
    "docker-compose.yml"
)

$configReplacements = @{
    "name = `"$OldName-ai`"" = "name = `"$NewName`""
    "name = `"$OldName`"" = "name = `"$NewName`""
    "$OldName = `"$OldName" = "$NewName = `"$NewName"
    "packages = [`"$OldName`"]" = "packages = [`"$NewName`"]"
    "`"$OldName`" = `"$OldName`"" = "`"$NewName`" = `"$NewName`""
    "$OldName/" = "$NewName/"
    "$OldName/**" = "$NewName/**"
    "$OldName contributors" = "$NewName contributors"
    "pip install $OldName" = "pip install $NewName"
    "${OldNameUpper}_" = "${NewNameUpper}_"
}

foreach ($file in $configFiles) {
    $filePath = Join-Path $ProjectPath $file
    if (Test-Path $filePath) {
        if (Update-FileContent -FilePath $filePath -Replacements $configReplacements) {
            Write-Host "  [Updated] $file" -ForegroundColor Green
        }
    }
}

# Step 4: Update documentation
Write-Host "`nStep 4: Updating documentation..." -ForegroundColor Yellow

$docReplacements = @{
    $OldName = $NewName
    "HKUDS/$NewName" = "zebbern/$NewName"  # Update GitHub references
    "${OldNameUpper}_" = "${NewNameUpper}_"
    ".$OldName" = ".$NewName"
}

$mdCount = Update-FilesInDirectory -Directory $ProjectPath -Extensions @(".md", ".rst", ".txt") -Replacements $docReplacements
Write-Host "  [Done] Updated $mdCount documentation files" -ForegroundColor Cyan

# Step 5: Update test files
Write-Host "`nStep 5: Updating test files..." -ForegroundColor Yellow
$testPath = Join-Path $ProjectPath "tests"
if (Test-Path $testPath) {
    $testCount = Update-FilesInDirectory -Directory $testPath -Extensions @(".py") -Replacements $pythonReplacements
    Write-Host "  [Done] Updated $testCount test files" -ForegroundColor Cyan
} else {
    Write-Host "  [Skip] No tests folder found" -ForegroundColor Gray
}

# Step 6: Environment files
Write-Host "`nStep 6: Updating environment files..." -ForegroundColor Yellow

$envFiles = @(".env", ".env.example", ".env.local", ".env.development")
$envReplacements = @{
    "${OldNameUpper}_" = "${NewNameUpper}_"
    $OldName = $NewName
}

foreach ($file in $envFiles) {
    $filePath = Join-Path $ProjectPath $file
    if (Test-Path $filePath) {
        if (Update-FileContent -FilePath $filePath -Replacements $envReplacements) {
            Write-Host "  [Updated] $file" -ForegroundColor Green
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Rename Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n[DRY RUN] No changes were made. Run without -DryRun to apply changes." -ForegroundColor Magenta
} else {
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Reinstall the package: pip install -e ." -ForegroundColor Gray
    Write-Host "  2. Test: python -m $NewName --version" -ForegroundColor Gray
    Write-Host "  3. Commit: git add -A && git commit -m 'Rename $OldName to $NewName'" -ForegroundColor Gray
}

Write-Host ""
