$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path -Parent $PSScriptRoot
$iconPath = Join-Path $projectRoot 'desktop\tb.ico'
$sizes = @(16, 20, 24, 32, 40, 48, 64, 128, 256)
$frames = @()
function ConvertTo-SvgPath($path) {
    $points=$path.PathPoints; $types=$path.PathTypes
    $parts=New-Object System.Collections.Generic.List[string]
    $culture=[System.Globalization.CultureInfo]::InvariantCulture
    for($i=0;$i -lt $points.Count;$i++) {
        $kind=$types[$i] -band 7
        if($kind -eq 3) {
            $coordinates=@()
            for($j=0;$j -lt 3;$j++) {$coordinates+=$points[$i+$j].X.ToString('0.###',$culture);$coordinates+=$points[$i+$j].Y.ToString('0.###',$culture)}
            $parts.Add('C'+($coordinates -join ' '));$i+=2
        } else {
            $command=if($kind -eq 0){'M'}else{'L'}
            $parts.Add($command+$points[$i].X.ToString('0.###',$culture)+' '+$points[$i].Y.ToString('0.###',$culture))
        }
        if(($types[$i] -band 128) -ne 0) {$parts.Add('Z')}
    }
    return $parts -join ' '
}
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
    $background = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#101116'))
    $toBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#9b8afb'))
    $beBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#efedf8'))
    $border = New-Object System.Drawing.Pen ([System.Drawing.ColorTranslator]::FromHtml('#2c2a3d')),24
    $font = New-Object System.Drawing.Font 'Segoe UI',340,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
    $format = [System.Drawing.StringFormat]::GenericTypographic.Clone()
    $format.Alignment = 'Center'
    $format.LineAlignment = 'Center'
    $graphics.FillPath($background,$shape)
    $graphics.DrawPath($border,$shape)
    $toPath = New-Object System.Drawing.Drawing2D.GraphicsPath
    $bePath = New-Object System.Drawing.Drawing2D.GraphicsPath
    $toWidth = $graphics.MeasureString('To',$font,[System.Drawing.PointF]::new(0,0),$format).Width
    $toPath.AddString('To',$font.FontFamily,[int][System.Drawing.FontStyle]::Bold,340,[System.Drawing.PointF]::new(0,0),$format)
    $bePath.AddString('Be',$font.FontFamily,[int][System.Drawing.FontStyle]::Bold,340,[System.Drawing.PointF]::new($toWidth,0),$format)
    $bounds = [System.Drawing.RectangleF]::Union($toPath.GetBounds(),$bePath.GetBounds())
    $translation = New-Object System.Drawing.Drawing2D.Matrix
    $translation.Translate((1024-$bounds.Width)/2-$bounds.X,(1024-$bounds.Height)/2-$bounds.Y)
    $toPath.Transform($translation); $bePath.Transform($translation)
    $graphics.FillPath($toBrush,$toPath)
    $graphics.FillPath($beBrush,$bePath)
    if($size -eq 256) {
        $toSvg=ConvertTo-SvgPath $toPath; $beSvg=ConvertTo-SvgPath $bePath
        $svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect x="24" y="24" width="976" height="976" rx="160" fill="#101116" stroke="#2c2a3d" stroke-width="24"/><path fill="#9b8afb" fill-rule="evenodd" d="'+$toSvg+'"/><path fill="#efedf8" fill-rule="evenodd" d="'+$beSvg+'"/></svg>'
        [System.IO.File]::WriteAllText((Join-Path $projectRoot 'frontend\public\tobe.svg'),$svg+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
    }
    $translation.Dispose(); $toPath.Dispose(); $bePath.Dispose()
    $small = New-Object System.Drawing.Bitmap $size,$size
    $scaled = [System.Drawing.Graphics]::FromImage($small)
    $scaled.CompositingQuality = 'HighQuality'
    $scaled.InterpolationMode = 'HighQualityBicubic'
    $scaled.PixelOffsetMode = 'HighQuality'
    $scaled.DrawImage($bitmap,0,0,$size,$size)
    $stream = New-Object System.IO.MemoryStream
    $small.Save($stream,[System.Drawing.Imaging.ImageFormat]::Png)
    $frames += ,$stream.ToArray()
    foreach ($resource in @($stream,$scaled,$small,$format,$font,$border,$toBrush,$beBrush,$background,$shape,$graphics,$bitmap)) { $resource.Dispose() }
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
