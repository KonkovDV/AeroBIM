# Fix GitHub "Unverified" on GPG key B5690EEEBB952194
#
# Symptom: key is uploaded, email shows noreply@github.com + Unverified.
# Cause: key UID is GitHub <noreply@github.com>, but commits use
#        KonkovDV@users.noreply.github.com — GitHub will not verify that UID.
#
# Run on the PC that HAS the secret key (the one that signed merges #12–#14):

$ErrorActionPreference = "Stop"
$gpg = "C:\Program Files\Git\usr\bin\gpg.exe"
if (-not (Test-Path $gpg)) { $gpg = "gpg" }

$keyId = "B5690EEEBB952194"
$uid = "KonkovDV <KonkovDV@users.noreply.github.com>"
$asc = Join-Path (Split-Path -Parent $PSScriptRoot) "governance\trusted_signing_keys\B5690EEEBB952194.asc"

Write-Host "Checking secret key $keyId ..."
$secrets = & $gpg --list-secret-keys --keyid-format long $keyId 2>&1 | Out-String
if ($secrets -notmatch $keyId) {
    Write-Host "ERROR: secret key not on this PC. Open the machine that signed PR merges, copy this script there, re-run."
    exit 1
}

Write-Host "Adding UID: $uid"
& $gpg --batch --yes --quick-add-uid $keyId $uid
if ($LASTEXITCODE -ne 0) {
    Write-Host "If UID already exists, continuing to export..."
}

Write-Host "Exporting public key -> $asc"
& $gpg --armor --export $keyId | Set-Content -Path $asc -Encoding ascii

Write-Host @"

DONE locally. Now in browser:
1) https://github.com/settings/keys  -> delete old "AeroBIM B5690"
2) New GPG key -> paste full contents of:
   $asc
3) https://github.com/settings/emails -> confirm KonkovDV@users.noreply.github.com is listed
   (enable "Keep my email addresses private" if you use the noreply address)
4) Back in C:\plans\AeroBIM:
   .\scripts\commit_staged_n43_signed.ps1
   git push origin HEAD
"@
