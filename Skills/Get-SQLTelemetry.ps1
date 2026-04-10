
param([string]$ServerInstance = "localhost") 


try {
    # 1. Check CPU Load via Ring Buffers
    $cpuQuery = "SELECT (SELECT TOP 1 100 - SystemIdle FROM (SELECT record.value('(./Record/SchedulerMonitorEvent/SystemIdle)[1]', 'int') AS SystemIdle FROM (SELECT CAST(record AS xml) AS record FROM sys.dm_os_ring_buffers WHERE ring_buffer_type = 'RING_BUFFER_SCHEDULER_MONITOR') AS x ORDER BY record.value('(./Record/@time)[1]', 'bigint') DESC) as y) AS CPU_Load"
    $cpuData = Invoke-Sqlcmd -ServerInstance $ServerInstance -Query $cpuQuery -ErrorAction Stop
    $cpu = $cpuData.CPU_Load

    # 2. Check for Blocked Processes (Deadlock indicators)
    $blockQuery = "SELECT COUNT(*) as BlockedCount FROM sys.dm_exec_requests WHERE blocking_session_id <> 0"
    $blockData = Invoke-Sqlcmd -ServerInstance $ServerInstance -Query $blockQuery
    $blocked = $blockData.BlockedCount

    # 3. Check Disk Space on Backup Drive (Assuming C: for dev environment)
    $disk = Get-Volume -DriveLetter C
    $diskFreeGB = [math]::Round($disk.SizeRemaining / 1GB, 2)

    # Determine Status
    $status = "HEALTHY"
    if ($cpu -gt 80) { $status = "CRITICAL_CPU" }
    elseif ($diskFreeGB -lt 5) { $status = "CRITICAL_DISK" }
    elseif ($blocked -gt 0) { $status = "WARNING_BLOCKS" }

    return @{ 
        Timestamp = (Get-Date).ToString("HH:mm:ss"); 
        CPU = $cpu; 
        BlockedSessions = $blocked;
        DiskFreeGB = $diskFreeGB;
        Status = $status 
    } | ConvertTo-Json -Compress

} catch {
    return @{ Status = "ERROR"; Message = "DB Connection Failed" } | ConvertTo-Json -Compress
}