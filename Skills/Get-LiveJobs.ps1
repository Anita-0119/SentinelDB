param([string]$ServerInstance = "localhost")

# Query SSMS for live Job Statuses
$query = @"
SELECT 
    j.name AS JobName,
    c.name AS Category,
    CASE h.run_status WHEN 0 THEN 'Failed' WHEN 1 THEN 'Succeeded' ELSE 'Unknown' END as Outcome
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.syscategories c ON j.category_id = c.category_id
LEFT JOIN msdb.dbo.sysjobhistory h ON j.job_id = h.job_id AND h.step_id = 0
"@

$liveJobs = Invoke-Sqlcmd -ServerInstance $ServerInstance -Query $query
return $liveJobs | ConvertTo-Jsons