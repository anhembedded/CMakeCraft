param (
    [switch]$Build,
    [switch]$Test,
    [switch]$Example,
    [switch]$Clean,
    [switch]$Lint,
    [switch]$Format,
    [switch]$Coverage,
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

if (-not ($Build -or $Test -or $Example -or $Clean -or $Lint -or $Format -or $Coverage)) { $All = $true }

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
        
        # Determine the best generator available
        $Generator = $null
        if (Get-Command "ninja" -ErrorAction SilentlyContinue) {
            $Generator = "Ninja"
        }
        elseif (Get-Command "nmake" -ErrorAction SilentlyContinue) {
            $Generator = "NMake Makefiles"
        }
        elseif ($env:OS -eq "Windows_NT") {
            # If no command-line tools are in PATH, CMake usually defaults to NMake and fails.
            # We check if cl.exe is available to see if we're in a dev environment.
            if (-not (Get-Command "cl.exe" -ErrorAction SilentlyContinue)) {
                Write-Host "`n[!] No C++ compiler (cl.exe) or build tool (ninja, nmake) found in PATH." -ForegroundColor Yellow
                Write-Host "[!] TIP: Please run this script from 'Developer PowerShell for VS'" -ForegroundColor Cyan
                Write-Host "    or 'Developer Command Prompt for VS' to enable build tools.`n" -ForegroundColor Cyan
            }
        }
        
        if ($Generator) { $BuildArgs += "-G", $Generator }
        if ($Example -or $All) { $BuildArgs += "-DBUILD_EXAMPLES=ON" } else { $BuildArgs += "-DBUILD_EXAMPLES=OFF" }
        if ($Coverage) { $BuildArgs += "-DENABLE_COVERAGE=ON" }
        
        Write-Host "Configuring..."
        & cmake $BuildArgs
        if ($LASTEXITCODE -ne 0) { 
            Write-Error "Configuration failed. Check if your compiler is correctly set up."
            throw "Configuration failed" 
        }

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

if ($Format -or $All) {
    Invoke-Step "Format Code" {
        if (Get-Command "clang-format" -ErrorAction SilentlyContinue) {
            Write-Host "Formatting source files..."
            $Files = Get-ChildItem -Path "$SourceDir/src", "$SourceDir/interface", "$SourceDir/inc" -Include *.cpp, *.h -Recurse -ErrorAction SilentlyContinue
            if ($Files) {
                foreach ($f in $Files) {
                    & clang-format -i $f.FullName
                }
            }
        }
        else {
            Write-Warning "clang-format not found. Skipping format step."
        }
    }
}

if ($Lint -or $All) {
    Invoke-Step "Static Analysis (Clang-Tidy)" {
        if (Get-Command "clang-tidy" -ErrorAction SilentlyContinue) {
            $DbPath = "$BuildDir/compile_commands.json"
            if (-not (Test-Path $DbPath)) {
                Write-Host "compile_commands.json not found. Running configuration first..."
                & cmake -S $SourceDir -B $BuildDir -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
            }
            
            $Files = Get-ChildItem -Path "$SourceDir/src" -Filter *.cpp -Recurse -ErrorAction SilentlyContinue
            if ($Files) {
                foreach ($f in $Files) {
                    Write-Host "Linting $($f.Name)..."
                    & clang-tidy $f.FullName -p $BuildDir --quiet
                }
            }
        }
        else {
            Write-Warning "clang-tidy not found. Skipping lint step."
        }
    }
}

if ($Coverage) {
    Invoke-Step "Code Coverage" {
        if ($env:OS -ne "Windows_NT") {
            if (Get-Command "lcov" -ErrorAction SilentlyContinue) {
                Write-Host "Generating coverage report..."
                & lcov --capture --directory . --output-file coverage.info
                & lcov --remove coverage.info '/usr/*' '*/tests/*' '*/examples/*' --output-file coverage.info
                & genhtml coverage.info --output-directory coverage_report
                Write-Host "Coverage report generated in: coverage_report/index.html" -ForegroundColor Green
            }
            else {
                Write-Warning "lcov not found. Skipping coverage."
            }
        }
        else {
            Write-Host "Native lcov is usually for Linux. For Windows coverage, use OpenCppCoverage or VS tools." -ForegroundColor Yellow
        }
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
