[CmdletBinding()]
param(
    [ValidateSet('up', 'down', 'check', 'test', 'frontend-test')]
    [string]$Action = 'up'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Push-Location $ProjectRoot

function Confirm-NativeCommand {
    if ($LASTEXITCODE -ne 0) {
        throw "The previous command failed with exit code $LASTEXITCODE."
    }
}

try {
    switch ($Action) {
        'up' {
            if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
            docker compose up --build
        }
        'down' { docker compose down }
        'test' {
            $frontendTest = 'corepack enable ' +
                '&& pnpm install --no-frozen-lockfile --store-dir /tmp/pnpm-store ' +
                '&& pnpm test'
            docker run --rm --volume "$ProjectRoot\backend:/workspace" --workdir /workspace `
                python:3.12-slim sh -c "pip install -e '.[dev]' && pytest"
            Confirm-NativeCommand
            docker run --rm --env CI=true `
                --volume "$ProjectRoot\frontend:/workspace" --workdir /workspace `
                node:22-alpine sh -c $frontendTest
            Confirm-NativeCommand
        }
        'frontend-test' {
            docker build --target test --tag avenward-frontend-test `
                --file frontend/Dockerfile .
            Confirm-NativeCommand
            docker run --rm --env CI=true avenward-frontend-test pnpm test
            Confirm-NativeCommand
        }
        'check' {
            $backendCheck = "pip install -e '.[dev]' && ruff format --check . " +
                '&& ruff check . && mypy app tests && pytest'
            $frontendCheck = 'failures=0; pnpm format || failures=1; ' +
                'pnpm lint || failures=1; ' +
                'pnpm exec tsc -b || failures=1; pnpm test || failures=1; ' +
                'pnpm build || failures=1; exit $failures'
            docker compose config --quiet
            Confirm-NativeCommand
            docker run --rm --volume "$ProjectRoot\backend:/workspace" --workdir /workspace `
                python:3.12-slim sh -c $backendCheck
            Confirm-NativeCommand
            docker build --target test --tag avenward-frontend-check `
                --file frontend/Dockerfile .
            Confirm-NativeCommand
            docker run --rm --env CI=true avenward-frontend-check sh -c $frontendCheck
            Confirm-NativeCommand
        }
    }
} finally {
    Pop-Location
}
