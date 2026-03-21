param(
    [int]$GraceSeconds = 2
)

$ErrorActionPreference = "SilentlyContinue"

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class WinApi {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindowEnabled(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd,
        uint Msg,
        UIntPtr wParam,
        IntPtr lParam,
        uint fuFlags,
        uint uTimeout,
        out UIntPtr lpdwResult
    );
}
"@

$WM_CLOSE = 0x0010
$SMTO_ABORTIFHUNG = 0x0002

$protectedNames = @(
    "explorer",
    "ShellExperienceHost",
    "SearchHost",
    "StartMenuExperienceHost",
    "sihost",
    "dwm",
    "winlogon",
    "csrss",
    "services",
    "lsass"
)

$windows = New-Object System.Collections.Generic.List[object]

$null = [WinApi]::EnumWindows({
    param($hWnd, $lParam)

    if (-not [WinApi]::IsWindowVisible($hWnd)) { return $true }
    if (-not [WinApi]::IsWindowEnabled($hWnd)) { return $true }

    $sb = New-Object System.Text.StringBuilder 1024
    [void][WinApi]::GetWindowText($hWnd, $sb, $sb.Capacity)
    $title = $sb.ToString().Trim()
    if ([string]::IsNullOrWhiteSpace($title)) { return $true }

    $pid = 0
    [void][WinApi]::GetWindowThreadProcessId($hWnd, [ref]$pid)
    if ($pid -le 0) { return $true }

    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($null -eq $proc) { return $true }
    if ($proc.Id -eq $PID) { return $true }
    if ($protectedNames -contains $proc.ProcessName) { return $true }

    $windows.Add([PSCustomObject]@{
        Handle = $hWnd
        PID = [int]$proc.Id
        Name = $proc.ProcessName
        Title = $title
    }) | Out-Null

    return $true
}, [IntPtr]::Zero)

# Close politely first
foreach ($w in $windows) {
    $result = [UIntPtr]::Zero
    [void][WinApi]::SendMessageTimeout(
        [IntPtr]$w.Handle,
        [uint32]$WM_CLOSE,
        [UIntPtr]::Zero,
        [IntPtr]::Zero,
        [uint32]$SMTO_ABORTIFHUNG,
        [uint32]1000,
        [ref]$result
    )
}

Start-Sleep -Seconds ([Math]::Max(1, $GraceSeconds))

# Force-close any remaining processes that still own a visible window
$remainingPids = New-Object System.Collections.Generic.HashSet[int]
$null = [WinApi]::EnumWindows({
    param($hWnd, $lParam)

    if (-not [WinApi]::IsWindowVisible($hWnd)) { return $true }

    $sb = New-Object System.Text.StringBuilder 1024
    [void][WinApi]::GetWindowText($hWnd, $sb, $sb.Capacity)
    $title = $sb.ToString().Trim()
    if ([string]::IsNullOrWhiteSpace($title)) { return $true }

    $pid = 0
    [void][WinApi]::GetWindowThreadProcessId($hWnd, [ref]$pid)
    if ($pid -gt 0) {
        [void]$remainingPids.Add([int]$pid)
    }

    return $true
}, [IntPtr]::Zero)

foreach ($pid in $remainingPids) {
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($null -eq $proc) { continue }
    if ($proc.Id -eq $PID) { continue }
    if ($protectedNames -contains $proc.ProcessName) { continue }

    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "[PyTrade] Close-all-windows routine finished."
