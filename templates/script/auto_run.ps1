param (
    [switch]$Build,
    [switch]$Test,
    [switch]$Example,
    [switch]$Clean,
    [string]$Config = "Debug",
    [switch]$Verbose,
    [switch]$All
)

function Test-CommandAvailability {
    param ([string]$CommandName)
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        Write-Error "Error: '$CommandName' is not installed or not in PATH."
        exit 1
    }
}

function Invoke-Step {
    param ([string]$StepName, [scriptblock]$Action)
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Running Step: $StepName" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    try {
        & $Action
        Write-Host "Step '$StepName' completed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Step '$StepName' failed: $_"
        exit 1
    }
}

if (-not ($Build -or $Test -or $Example -or $Clean)) { $All = $true }

Test-CommandAvailability "cmake"
$SourceDir = $PSScriptRoot + "/.."
$BuildDir = "$SourceDir/build"

if ($Clean -or $All) {
    Invoke-Step "Clean" {
        if (Test-Path $BuildDir) { Remove-Item -Path $BuildDir -Recurse -Force }
    }
}

if ($Build -or $All) {
    Invoke-Step "Configure and Build" {
        $BuildArgs = @("-S", $SourceDir, "-B", $BuildDir, "-DCMAKE_BUILD_TYPE=$Config")
        if (Get-Command "ninja" -ErrorAction SilentlyContinue) { $BuildArgs += "-GNinja" }
        if ($Example -or $All) { $BuildArgs += "-DBUILD_EXAMPLES=ON" } else { $BuildArgs += "-DBUILD_EXAMPLES=OFF" }
        
        Write-Host "Configuring..."
        & cmake $BuildArgs
        if ($LASTEXITCODE -ne 0) { throw "Configuration failed" }

        Write-Host "Building..."
        $BuildCmd = @("--build", $BuildDir, "--config", $Config)
        if ($Verbose) { $BuildCmd += "--verbose" }
        & cmake $BuildCmd
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    }
}

if ($Test -or $All) {
    Invoke-Step "Run Tests" {
        & ctest --test-dir $BuildDir -C $Config --output-on-failure
        if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    }
}

if ($Example -or $All) {
    Invoke-Step "Run Example" {
        $PossiblePaths = @(
            "$BuildDir/examples/$Config/{{PROJECT_NAME}}_example.exe",
            "$BuildDir/examples/{{PROJECT_NAME}}_example.exe",
            "$BuildDir/examples/$Config/{{PROJECT_NAME}}_example",
            "$BuildDir/examples/{{PROJECT_NAME}}_example"
        )
        $ExePath = $null
        foreach ($p in $PossiblePaths) { if (Test-Path $p) { $ExePath = $p; break } }
        if ($ExePath) { & $ExePath } else { throw "Example executable not found." }
    }
}

Write-Host "All requested steps completed successfully!" -ForegroundColor Green
exit 0
