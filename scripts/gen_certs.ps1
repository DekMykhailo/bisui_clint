$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$CertDir = if ($env:CERT_DIR) { $env:CERT_DIR } else { Join-Path $Root "certs" }
$Days = if ($env:DAYS) { $env:DAYS } else { "365" }
$Cn = if ($env:CN) { $env:CN } else { "localhost" }
$Force = $env:FORCE -eq "1"

New-Item -ItemType Directory -Force -Path $CertDir | Out-Null
$Cert = Join-Path $CertDir "cert.pem"
$Key = Join-Path $CertDir "key.pem"

if ((Test-Path $Cert) -and (Test-Path $Key) -and -not $Force) {
    Write-Host "Certs already exist at $CertDir (set FORCE=1 to overwrite)."
    exit 0
}

$openssl = $null
foreach ($candidate in @(
    "openssl",
    "C:\Program Files\Git\usr\bin\openssl.exe",
    "C:\Program Files\Git\mingw64\bin\openssl.exe"
)) {
    if ($candidate -eq "openssl") {
        $cmd = Get-Command openssl -ErrorAction SilentlyContinue
        if ($cmd) { $openssl = $cmd.Source; break }
    } elseif (Test-Path $candidate) {
        $openssl = $candidate
        break
    }
}

if (-not $openssl) {
    Write-Error "openssl not found. Install Git for Windows or OpenSSL and retry."
}

& $openssl req -x509 -newkey rsa:2048 -nodes `
    -keyout $Key `
    -out $Cert `
    -days $Days `
    -subj "/CN=$Cn" `
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

Write-Host "Wrote $Cert and $Key"
