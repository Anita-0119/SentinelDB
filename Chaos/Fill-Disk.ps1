# Instantly creates a 10GB file to trigger a Disk Full / Log Full scenario
$FilePath = "C:\SQLBackups\dummy_load.dat"
fsutil file createnew $FilePath 10737418240
Write-Host "Chaos injected: $FilePath created." -ForegroundColor Red