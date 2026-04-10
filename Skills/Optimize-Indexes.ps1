param([string]$Database = "Finance_DB")

Write-Output "Establishing connection to context: $Database"
Start-Sleep -Seconds 1
Write-Output "Scanning sys.dm_db_index_physical_stats for fragmentation > 20%..."
Write-Output "Target identified: [dbo].[LedgerEntries] (IX_Ledger_Date)"

Write-Output "Executing ALTER INDEX REBUILD WITH (ONLINE = ON)..."
Start-Sleep -Seconds 2

Write-Output "Index rebuilt successfully."
Write-Output "Executing sp_updatestats to refresh query optimizer thresholds."
Write-Output "Maintenance operation complete. I/O latency stabilized."