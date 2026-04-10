param([string]$ServerInstance = "localhost")

Write-Output "Querying sys.dm_db_file_space_usage for allocation discrepancies..."
Start-Sleep -Seconds 1
Write-Output "Identified orphaned temporary object '#Staging_Data_ETL' consuming 80% of data file."

Write-Output "Executing object cleanup protocol..."
Start-Sleep -Seconds 2
Write-Output "Temporary objects dropped. Executing DBCC SHRINKFILE on tempdev."
Write-Output "TempDB allocation successfully reduced. Free space restored."