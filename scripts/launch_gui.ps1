param([string]$Python = '')
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
  $bundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe'
  if (Test-Path $bundled) { $Python = $bundled }
  else {
    $command = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($command) { $Python = $command.Source }
    else { $Python = 'py.exe' }
  }
}
$env:PYTHONPATH = Join-Path $project 'src'
if ([IO.Path]::GetFileNameWithoutExtension($Python) -eq 'py') {
  Start-Process -FilePath $Python -ArgumentList @('-3w', '-m', 'idf_analyzer.gui') -WorkingDirectory $project
} else {
  Start-Process -FilePath $Python -ArgumentList @('-m', 'idf_analyzer.gui') -WorkingDirectory $project
}

