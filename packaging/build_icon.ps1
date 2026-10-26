$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path -Parent $PSScriptRoot
$iconPath = Join-Path $projectRoot 'desktop\tb.ico'
$sizes = @(16, 20, 24, 32, 40, 48, 64, 128, 256)
$frames = @()
foreach ($size in $sizes) {
    $bitmap = New-Object System.Drawing.Bitmap 1024,1024
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = 'AntiAlias'
    $graphics.TextRenderingHint = 'AntiAliasGridFit'
    $shape = New-Object System.Drawing.Drawing2D.GraphicsPath
    $shape.AddArc(24,24,320,320,180,90)
    $shape.AddArc(680,24,320,320,270,90)
    $shape.AddArc(680,680,320,320,0,90)
    $shape.AddArc(24,680,320,320,90,90)
    $shape.CloseFigure()
    $background = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#173039'))
    $letters = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#8be0cb'))
    $border = New-Object System.Drawing.Pen ([System.Drawing.ColorTranslator]::FromHtml('#467b7b')),24
    $font = New-Object System.Drawing.Font 'Segoe UI',400,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
    $format = [System.Drawing.StringFormat]::GenericTypographic.Clone()
    $format.Alignment = 'Center'
    $format.LineAlignment = 'Center'
    $graphics.FillPath($background,$shape)
    $graphics.DrawPath($border,$shape)
    $graphics.DrawString('To',$font,$letters,[System.Drawing.RectangleF]::new(30,0,964,550),$format)
    $graphics.DrawString('Be',$font,$letters,[System.Drawing.RectangleF]::new(30,415,964,550),$format)
    $small = New-Object System.Drawing.Bitmap $size,$size
    $scaled = [System.Drawing.Graphics]::FromImage($small)
    $scaled.CompositingQuality = 'HighQuality'
    $scaled.InterpolationMode = 'HighQualityBicubic'
    $scaled.PixelOffsetMode = 'HighQuality'
    $scaled.DrawImage($bitmap,0,0,$size,$size)
    $stream = New-Object System.IO.MemoryStream
    $small.Save($stream,[System.Drawing.Imaging.ImageFormat]::Png)
    $frames += ,$stream.ToArray()
    foreach ($resource in @($stream,$scaled,$small,$format,$font,$border,$letters,$background,$shape,$graphics,$bitmap)) { $resource.Dispose() }
}
$output = [System.IO.File]::Create($iconPath)
$writer = New-Object System.IO.BinaryWriter $output
try {
    $writer.Write([UInt16]0); $writer.Write([UInt16]1); $writer.Write([UInt16]$frames.Count)
    $offset = 6 + 16 * $frames.Count
    for ($i=0; $i -lt $frames.Count; $i++) {
        $dimension = if ($sizes[$i] -eq 256) {0} else {$sizes[$i]}
        $writer.Write([byte]$dimension); $writer.Write([byte]$dimension)
        $writer.Write([byte]0); $writer.Write([byte]0)
        $writer.Write([UInt16]1); $writer.Write([UInt16]32)
        $writer.Write([UInt32]$frames[$i].Length); $writer.Write([UInt32]$offset)
        $offset += $frames[$i].Length
    }
    foreach ($frame in $frames) { $writer.Write([byte[]]$frame) }
} finally { $writer.Dispose(); $output.Dispose() }
Write-Output 'ToBe icon generated with nine Windows icon sizes.'
