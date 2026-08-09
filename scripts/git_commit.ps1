# Commit helper. Prefer real authorship metadata (including Co-authored-by when true).
param(
    [Parameter(Mandatory = $true)]
    [string]$Message
)

git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
