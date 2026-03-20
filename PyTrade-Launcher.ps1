# PyTrade Modern Launcher - PowerShell
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File "PyTrade-Launcher.ps1"

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$projectRoot = Split-Path -Path $PSCommandPath -Parent

function Start-CommandFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $target = Join-Path $projectRoot $RelativePath
    if (-not (Test-Path $target)) {
        [System.Windows.Forms.MessageBox]::Show(
            "File not found: $RelativePath",
            "PyTrade Launcher",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
        return
    }

    Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "`"$target`"") -WorkingDirectory $projectRoot
}

function New-MenuButton {
    param(
        [string]$Text,
        [int]$Top,
        [int]$Width = 510,
        [int]$Height = 44,
        [int]$Left = 16,
        [System.Drawing.Color]$BackColor = [System.Drawing.Color]::FromArgb(0, 102, 204),
        [ScriptBlock]$OnClick
    )

    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $button.Left = $Left
    $button.Top = $Top
    $button.Width = $Width
    $button.Height = $Height
    $button.BackColor = $BackColor
    $button.ForeColor = [System.Drawing.Color]::White
    $button.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $button.FlatAppearance.BorderSize = 0
    $button.Cursor = [System.Windows.Forms.Cursors]::Hand
    $button.Add_Click($OnClick)
    return $button
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "PyTrade Control Center"
$form.Width = 550
$form.Height = 510
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

$header = New-Object System.Windows.Forms.Label
$header.Text = "PyTrade Control Center"
$header.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$header.ForeColor = [System.Drawing.Color]::FromArgb(0, 102, 204)
$header.Left = 16
$header.Top = 20
$header.Width = 510
$header.Height = 38

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = "Launch, repair, and manage PyTrade from one place."
$subtitle.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$subtitle.ForeColor = [System.Drawing.Color]::FromArgb(80, 80, 80)
$subtitle.Left = 16
$subtitle.Top = 56
$subtitle.Width = 520
$subtitle.Height = 22

$buttons = @(
    (New-MenuButton -Text "Install / Repair" -Top 92 -BackColor ([System.Drawing.Color]::FromArgb(59, 130, 246)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "scripts\OneClick-Setup.bat"
    }),
    (New-MenuButton -Text "Start All (Daemon + Dashboard)" -Top 142 -BackColor ([System.Drawing.Color]::FromArgb(16, 185, 129)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "Start-All.bat"
    }),
    (New-MenuButton -Text "Dashboard Only" -Top 192 -BackColor ([System.Drawing.Color]::FromArgb(14, 165, 233)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "Run-Dashboard.bat"
    }),
    (New-MenuButton -Text "Daemon Only" -Top 242 -BackColor ([System.Drawing.Color]::FromArgb(245, 158, 11)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "Run-Daemon.bat"
    }),
    (New-MenuButton -Text "Create Desktop Shortcuts" -Top 292 -BackColor ([System.Drawing.Color]::FromArgb(107, 114, 128)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "Create-Desktop-Shortcuts-Enhanced.bat"
    }),
    (New-MenuButton -Text "Status Check" -Top 342 -BackColor ([System.Drawing.Color]::FromArgb(124, 58, 237)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "Status-Check.bat"
    }),
    (New-MenuButton -Text "Open Logs" -Top 392 -BackColor ([System.Drawing.Color]::FromArgb(17, 24, 39)) -OnClick {
        $form.Close()
        Start-CommandFile -RelativePath "Open-Logs.bat"
    })
)

$form.Controls.Add($header)
$form.Controls.Add($subtitle)
foreach ($btn in $buttons) { $form.Controls.Add($btn) }

[void]$form.ShowDialog()
