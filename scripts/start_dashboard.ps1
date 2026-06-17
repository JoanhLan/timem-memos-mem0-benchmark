# Start Benchmark Lab (builds frontend if needed)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
python main.py dashboard @args
