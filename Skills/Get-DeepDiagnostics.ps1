param([string]$ServerInstance = "localhost")

$query = @"
SELECT TOP 3
    r.session_id AS SPID,
    r.blocking_session_id AS Blocker_SPID,
    r.total_elapsed_time / 1000 AS DurationSec,
    r.cpu_time AS CPUTime,
    SUBSTRING(t.text, 1, 100) AS CommandSnippet
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.session_id > 50 AND r.session_id <> @@SPID
ORDER BY r.cpu_time DESC
"@

$diagnostics = Invoke-Sqlcmd -ServerInstance $ServerInstance -Query $query

if ($null -eq $diagnostics) { return @() | ConvertTo-Json -Compress }
return @($diagnostics) | ConvertTo-Json -Compress