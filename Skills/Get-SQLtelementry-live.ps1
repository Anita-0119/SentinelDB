param([string]$ServerInstance = "localhost")
$payload = @{
    CPU = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
    DiskFreeGB = Get-WmiObject Win32_LogicalDisk | Where-Object DeviceID -eq "F:" | Select-Object -ExpandProperty FreeSpace | % { [math]::Round($_ / 1GB, 2) }
    JobFailures = Invoke-Sqlcmd -Query "SELECT name FROM msdb.dbo.sysjobs j JOIN msdb.dbo.sysjobhistory h ON j.job_id = h.job_id WHERE h.run_status = 0"
}
$payload | ConvertTo-Json