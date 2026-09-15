param (
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$false)]
    [string]$Description = "Plugin description",

    [Parameter(Mandatory=$false)]
    [string]$Category = "productivity"
)

$PluginDir = Join-Path $PSScriptRoot "plugins\$Name"

if (Test-Path $PluginDir) {
    Write-Error "Plugin directory already exists: $PluginDir"
    exit 1
}

Write-Host "Creating plugin scaffold at $PluginDir..."

# 1. Directories
New-Item -ItemType Directory -Path (Join-Path $PluginDir ".claude-plugin") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PluginDir "skills\$Name") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PluginDir "commands") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PluginDir "agents") -Force | Out-Null

# 2. Claude Code plugin.json (canonical schema)
$ClaudePlugin = @{
    name = $Name
    description = $Description
    version = "1.0.0"
    author = @{
        name = "Shanewas Ahmed"
        email = "shanewasahmed@gmail.com"
    }
} | ConvertTo-Json -Depth 5
Set-Content -Path (Join-Path $PluginDir ".claude-plugin\plugin.json") -Value $ClaudePlugin

# 3. Antigravity gemini-extension.json
$GeminiExt = @{
    name = $Name
    description = $Description
    version = "1.0.0"
    contextFileName = "GEMINI.md"
} | ConvertTo-Json -Depth 5
Set-Content -Path (Join-Path $PluginDir "gemini-extension.json") -Value $GeminiExt

# 4. OpenCode package.json and plugin.js
$PkgJson = @{
    name = "@shanewas/plugin-$Name"
    version = "1.0.0"
    description = $Description
    author = "Shanewas Ahmed <shanewasahmed@gmail.com>"
    license = "MIT"
    main = "plugin.js"
    dependencies = @{
        "@opencode-ai/plugin" = "^1.17.8"
    }
} | ConvertTo-Json -Depth 5
Set-Content -Path (Join-Path $PluginDir "package.json") -Value $PkgJson

$PluginJs = @"
export const plugin = async (ctx) => {
  return {
    name: "$Name",
    description: "$Description",
    version: "1.0.0"
  };
};
"@
Set-Content -Path (Join-Path $PluginDir "plugin.js") -Value $PluginJs

# 5. Starter SKILL.md
$SkillMd = @"
---
name: $Name
description: $Description
---

# $Name Skill

$Description
"@
Set-Content -Path (Join-Path $PluginDir "skills\$Name\SKILL.md") -Value $SkillMd

# 6. Update root .claude-plugin/marketplace.json
$MarketplacePath = Join-Path $PSScriptRoot ".claude-plugin\marketplace.json"
$Marketplace = Get-Content $MarketplacePath -Raw | ConvertFrom-Json

$NewEntry = [PSCustomObject]@{
    name = $Name
    description = $Description
    version = "1.0.0"
    author = [PSCustomObject]@{
        name = "Shanewas Ahmed"
        email = "shanewasahmed@gmail.com"
    }
    source = "./plugins/$Name"
    category = $Category
    homepage = "https://github.com/shanewas/shanewas-plugins"
}

$Marketplace.plugins += $NewEntry
$Marketplace | ConvertTo-Json -Depth 10 | Set-Content -Path $MarketplacePath

Write-Host "Plugin '$Name' created and registered in .claude-plugin/marketplace.json!"
