param(
    [string]$SpaceName = "urbaneye",
    [string]$Username = "",
    [string]$Token = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git is not installed. Install it from https://git-scm.com and re-run."
    exit 1
}

if (-not $Username) { $Username = Read-Host "Your Hugging Face username" }
if (-not $Token) {
    $sec = Read-Host "Your Hugging Face WRITE token (Settings > Access Tokens)" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    $Token = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
}

$repoUrl = "https://$Username`:$Token@huggingface.co/spaces/$Username/$SpaceName"
$tmp = Join-Path $env:TEMP "urbaneye_hf_space_$([guid]::NewGuid().ToString('N'))"

Write-Host "Cloning space $Username/$SpaceName (create it first in the HF dashboard) ..."
git clone $repoUrl $tmp
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: could not clone. Did you create the Space with SDK 'Docker' first?"
    exit 1
}

Write-Host "Cleaning space and copying Dockerfile + README.md ..."
Get-ChildItem -LiteralPath $tmp -Force | Remove-Item -Recurse -Force
Copy-Item -LiteralPath (Join-Path $scriptDir "Dockerfile") -Destination $tmp
Copy-Item -LiteralPath (Join-Path $scriptDir "README.md") -Destination $tmp

git -C $tmp add -A
git -C $tmp commit -m "Deploy UrbanEye backend (Docker)"
git -C $tmp push

Write-Host ""
Write-Host "Pushed. The Space is now building."
Write-Host "Watch it at: https://huggingface.co/spaces/$Username/$SpaceName"
Write-Host "When done, the app will be at: https://$Username-$SpaceName.hf.space"