$procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'wave_chain|shard_worker|mass_seed|merge_pool' }
foreach ($p in $procs) {
    Write-Output ("KILL " + $p.ProcessId)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Write-Output ("killed: " + @($procs).Count)
