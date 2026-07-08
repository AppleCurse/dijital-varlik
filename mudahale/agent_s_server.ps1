# Agent S — Windows Masaustu Koprusu (TCP Sunucu)
param(
    [int]$Port = 9999
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$server = [System.Net.Sockets.TcpListener]$Port
$server.Start()
Write-Host "=== Agent S Windows Sunucusu Baslatildi (Port: $Port) ===" -ForegroundColor Green
Write-Host "WSL'den komut bekleniyor..." -ForegroundColor Cyan

try {
    while ($true) {
        $client = $server.AcceptTcpClient()
        $stream = $client.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $writer = New-Object System.IO.StreamWriter($stream)
        $writer.AutoFlush = $true

        $raw = $reader.ReadLine()
        if ($raw) {
            Write-Host "Gelen Komut: " -NoNewline -ForegroundColor Gray
            Write-Host $raw -ForegroundColor White
            
            $cmd = ConvertFrom-Json $raw
            $result = "error"
            $msg = ""

            switch ($cmd.action) {
                "ping" {
                    $computer = $env:COMPUTERNAME
                    $tarih = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
                    $result = "ok"
                    $msg = "pong|$computer|$tarih"
                }
                "open" {
                    try {
                        switch ($cmd.target) {
                            "excel"   { [System.Diagnostics.Process]::Start("excel.exe"); $result = "ok" }
                            "word"    { [System.Diagnostics.Process]::Start("winword.exe"); $result = "ok" }
                            "notepad" { [System.Diagnostics.Process]::Start("notepad.exe"); $result = "ok" }
                            "calc"    { [System.Diagnostics.Process]::Start("calc.exe"); $result = "ok" }
                            "browser" { [System.Diagnostics.Process]::Start("chrome.exe", $cmd.text); $result = "ok" }
                            default   { [System.Diagnostics.Process]::Start($cmd.target); $result = "ok" }
                        }
                        $msg = "$($cmd.target) basariyla acildi"
                    } catch {
                        $result = "error"
                        $msg = "Ugulama acilamadi: $_"
                    }
                }
                "press" {
                    try {
                        [System.Windows.Forms.SendKeys]::SendWait($cmd.target)
                        $result = "ok"
                        $msg = "Tuslar gonderildi: $($cmd.target)"
                    } catch {
                        $result = "error"
                        $msg = "Tus gonderim hatasi: $_"
                    }
                }
                "type" {
                    try {
                        [System.Windows.Forms.SendKeys]::SendWait($cmd.text)
                        $result = "ok"
                        $msg = "Metin yazildi"
                    } catch {
                        $result = "error"
                        $msg = "Yazma hatasi: $_"
                    }
                }
                "click" {
                    try {
                        $coords = $cmd.target.Split(',')
                        $x = [int]$coords[0]
                        $y = [int]$coords[1]
                        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
                        
                        # Mouse click simülasyonu (user32.dll)
                        $signature = '[DllImport("user32.dll")] public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);'
                        $type = Add-Type -MemberDefinition $signature -Name "Win32Mouse" -Namespace "Win32" -PassThru
                        $type::mouse_event(0x0002, 0, 0, 0, 0) # Left Down
                        $type::mouse_event(0x0004, 0, 0, 0, 0) # Left Up
                        $result = "ok"
                        $msg = "Tiklandi: $x,$y"
                    } catch {
                        $result = "error"
                        $msg = "Tiklama hatasi: $_"
                    }
                }
                "screen" {
                    try {
                        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                        $bmp = New-Object System.Drawing.Bitmap([int]$bounds.Width, [int]$bounds.Height)
                        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
                        $graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bmp.Size)
                        
                        $ms = New-Object System.IO.MemoryStream
                        $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Jpeg)
                        $bytes = $ms.ToArray()
                        $base64 = [Convert]::ToBase64String($bytes)
                        
                        $graphics.Dispose()
                        $bmp.Dispose()
                        $ms.Dispose()
                        
                        $result = "ok"
                        $msg = $base64
                    } catch {
                        $result = "error"
                        $msg = "Ekran goruntusu hatasi: $_"
                    }
                }
                default {
                    $result = "error"
                    $msg = "Bilinmeyen eylem: $($cmd.action)"
                }
            }

            $response = @{ status = $result; result = $msg } | ConvertTo-Json -Compress
            $writer.WriteLine($response)
        }

        $reader.Close()
        $writer.Close()
        $client.Close()
    }
} catch {
    Write-Host "Sistem Hatasi: $_" -ForegroundColor Red
} finally {
    $server.Stop()
}
