param(
    [string]$ServerInstance = "localhost", 
    [int]$SPID
)

if ($SPID -le 50) {
    Write-Output "GUARDRAIL INTERVENTION: Cannot terminate system process (SPID: $SPID). Aborting."
    exit 1
}

Write-Output "Admin authorization verified. Establishing connection to $ServerInstance..."
Start-Sleep -Seconds 1
Write-Output "Executing KILL command for SPID $SPID..."
Start-Sleep -Seconds 2

# Simulated execution
Write-Output "Process $SPID successfully terminated. Rolling back uncommitted transactions."
Write-Output "Schema locks released. CPU telemetry returning to baseline."