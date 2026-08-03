Add-Type -AssemblyName System.Drawing
$templatePath = "c:\Users\Zred\Desktop\中一班我来显身手：主题中审议调整单.docx"
$word = New-Object -ComObject Word.Application; $word.Visible = $false
$tmpDir = "C:\Users\Zred\Desktop\first CC\tmp_mindmaps"

function New-MindMap($themeName, $branches, $outputPath) {
    $width=800;$height=480;$bmp=New-Object System.Drawing.Bitmap($width,$height)
    $g=[System.Drawing.Graphics]::FromImage($bmp);$g.SmoothingMode="HighQuality";$g.TextRenderingHint="AntiAlias";$g.Clear([System.Drawing.Color]::White)
    $fR=New-Object System.Drawing.Font("Microsoft YaHei",12,[System.Drawing.FontStyle]::Bold)
    $fB=New-Object System.Drawing.Font("Microsoft YaHei",9,[System.Drawing.FontStyle]::Bold)
    $fL=New-Object System.Drawing.Font("Microsoft YaHei",7.5)
    $cols=@([System.Drawing.Color]::FromArgb(68,114,196),[System.Drawing.Color]::FromArgb(237,125,49),[System.Drawing.Color]::FromArgb(112,173,71),[System.Drawing.Color]::FromArgb(255,192,0))
    $pL=New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(180,180,180),2)
    $bRt=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(47,84,150))
    $bBg=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(214,228,245))
    $bBl=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(50,50,50))
    $bGr=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(100,100,100))
    $rs=$g.MeasureString($themeName,$fR);$rx=($width-$rs.Width)/2-10;$ry=8;$rw=$rs.Width+20;$rh=30
    $g.FillRectangle($bBg,$rx,$ry,$rw,$rh);$g.DrawRectangle($pL,$rx,$ry,$rw,$rh);$g.DrawString($themeName,$fR,$bRt,$rx+10,$ry+6)
    $rcx=$rx+$rw/2;$rbot=$ry+$rh;$bc=$branches.Count;$bw=[Math]::Floor(($width-40)/$bc)
    for($bi=0;$bi -lt $bc;$bi++){$br=$branches[$bi];$co=$cols[$bi%4];$pc=New-Object System.Drawing.Pen($co,2);$bc2=New-Object System.Drawing.SolidBrush($co);$bl=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(245,245,255))
    $bx=10+$bi*$bw;$bw2=$bw-8;$sz=$g.MeasureString($br.Title,$fB);$btX=$bx+[Math]::Max(0,($bw2-$sz.Width)/2-8);$btW=$sz.Width+16;$btY=$rbot+16;$btH=26
    $g.FillRectangle($bl,$btX,$btY,$btW,$btH);$g.DrawRectangle($pc,$btX,$btY,$btW,$btH);$g.DrawString($br.Title,$fB,$bc2,$btX+8,$btY+4)
    $g.DrawLine($pL,$rcx,$rbot,$btX+$btW/2,$btY);$sy=$btY+$btH+8
    foreach($gr in $br.Groups){if($sy+30 -gt $height-8){break};$g.DrawString($gr.Name,$fL,$bc2,$bx+4,$sy);$sy+=16
    if($gr.Items.Count -gt 0){$it=[string]::Join("  ",$gr.Items[0..[Math]::Min($gr.Items.Count-1,5)]);$g.DrawString($it,$fL,$bGr,$bx+8,$sy);$sy+=16};$sy+=3}
    $pc.Dispose();$bc2.Dispose();$bl.Dispose()}
    $fR.Dispose();$fB.Dispose();$fL.Dispose();$pL.Dispose();$bRt.Dispose();$bBg.Dispose();$bBl.Dispose();$bGr.Dispose();$g.Dispose()
    $bmp.Save($outputPath,[System.Drawing.Imaging.ImageFormat]::Png);$bmp.Dispose()
}

# ====== 春天里 (3 entries) ======
$outPath = "c:\Users\Zred\Desktop\2025-2小四班主题审议\2.春天里：中审议\春天里：主题中审议调整单.docx"
Copy-Item $templatePath $outPath -Force; $doc=$word.Documents.Open($outPath); $tbl=$doc.Tables.Item(1)

# Entry 1
$tbl.Cell(2,2).Range.Text="2025年3月30日u20144月11日（第5-6周）"
$tbl.Cell(3,2).Range.Text="春天里 u2014 小花小草"
$tbl.Cell(4,2).Range.Text="（一）兴趣`r`n1.u201c小花园u201d参观中幼儿对春天花朵表现出极大惊喜，主动用多种感官探索。`r`n2.u201c小草醒来了u201d后幼儿在户外自发蹲下摸小草说u201c软软的u201d。`r`n3.u201c亲亲小草u201d探玩中对碾碎小草出汁充满好奇。`r`n4.u201c花儿朵朵u201d水粉画中大胆运用色彩，作品表现力丰富。`r`n（二）能力`r`n1.多感官观察：约70%能运用视觉触觉嗅觉感知春天植物特征。`r`n2.语言表达：大部分能完整跟念u201c小草醒来了u201d，部分能仿编句式。`r`n3.美术表现：能有意识地选择颜色和形状进行表达。`r`n4.音乐感知：约60%能区分A段生长和B段春风的旋律变化。"
$tbl.Cell(5,2).Range.Text="有生成活动：`r`n1.u201c小草标本集u201d：将采集小草压制成标本制作班级图鉴。`r`n2.u201c花瓣收藏家u201d：收集落地花瓣分类装瓶放科学区观察。"
$sh=$tbl.Cell(6,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()}
$rng=$tbl.Cell(6,2).Range;$rng.Collapse(0)
$mp1="$tmpDir\spring_e1.png"
New-MindMap "春天里·小花小草(上)" @(@{Title="观察感知";Groups=@(@{Name="植物";Items=@("小花园","春天的草","亲亲小草","花园漫步")})},@{Title="语言艺术";Groups=@(@{Name="文学";Items=@("小草醒来了(语)","小草醒来了(音)","绿头发")},@{Name="美术";Items=@("花儿朵朵","柳树宝宝","越开越大花")})},@{Title="社会健康";Groups=@(@{Name="实践";Items=@("护草行动","花好看不摘","花仙子","蚂蚁搬豆子")})}) $mp1
$doc.InlineShapes.AddPicture($mp1,$false,$true,$rng)
$tbl.Cell(7,2).Range.Text="问题：`r`n1.户外观察时部分幼儿注意力被操场活动吸引。`r`n2.个别幼儿将小草放入口中存在安全隐患。`r`n3.水粉画颜料稀释不当导致画面过湿。`r`n解决方法：`r`n1.使用任务卡聚焦注意力。`r`n2.用儿歌建立安全边界：手拿鼻闻眼看不放嘴巴。`r`n3.教师提前测试颜料浓度并准备备用干画纸。"

# Add entries 2 and 3
for($entry=2;$entry -le 3;$entry++){
    $lr=$tbl.Rows.Count
    for($i=0;$i -lt 7;$i++){$tbl.Rows.Add()}
    if($entry -eq 2){
        $tbl.Cell($lr+1,1).Range.Text="中审议时间"; $tbl.Cell($lr+1,2).Range.Text="2025年4月14日u20144月25日（第7-8周）"
        try{$tbl.Cell($lr+1,1).Shading.BackgroundPatternColor=15132390;$tbl.Cell($lr+1,2).Shading.BackgroundPatternColor=15132390}catch{}
        $tbl.Cell($lr+2,1).Range.Text="主题名称"; $tbl.Cell($lr+2,2).Range.Text="春天里 u2014 小花小草/找春天"
        $tbl.Cell($lr+3,1).Range.Text="幼儿在主题中的行为表现"
        $tbl.Cell($lr+3,2).Range.Text="（一）兴趣`r`n1.u201c会画画的小草u201d创作中对小草替代画笔感到新奇。`r`n2.u201c护草行动u201d后主动提醒同伴不能踩草地。`r`n3.u201c花儿与蝴蝶u201d边听音乐边画画格外投入。`r`n4.u201c春天的电话u201d故事表演中代入感强烈。`r`n（二）能力`r`n1.环保意识：约75%能说至少2种保护花草方法。`r`n2.模式认知：约65%能正确复制延续ABAB模式。`r`n3.身体协调：手膝爬行和躲闪跑能力明显增强。`r`n4.艺术创想：尝试拖线画拓印画听音画等多种形式。"
        $tbl.Cell($lr+4,1).Range.Text="是否有生成活动"; $tbl.Cell($lr+4,2).Range.Text="有生成活动：`r`n1.u201c春天的花园u201d建构：用积木搭建春天花园。`r`n2.u201c护绿小卫士u201d挂牌：设计护绿标语牌挂在幼儿园。"
        $tbl.Cell($lr+5,1).Range.Text="重新架构的网络图"
        $sh=$tbl.Cell($lr+5,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()}
        $rg=$tbl.Cell($lr+5,2).Range;$rg.Collapse(0)
        $mp2="$tmpDir\spring_e2.png"
        New-MindMap "春天里·小花小草(下)" @(@{Title="小花小草(完)";Groups=@(@{Name="创意";Items=@("会画画草","花儿蝴蝶","小花匠")},@{Name="数学";Items=@("春天的花园","花仙子")})},@{Title="找春天(启)";Groups=@(@{Name="体验";Items=@("春天电话","明天春游","春游探玩")})},@{Title="生成";Groups=@(@{Name="环境";Items=@("花园建构","护绿卫士")})}) $mp2
        $doc.InlineShapes.AddPicture($mp2,$false,$true,$rg)
        $tbl.Cell($lr+6,1).Range.Text="问题与解决"
        $tbl.Cell($lr+6,2).Range.Text="问题：`r`n1.u201c花儿好看不摘u201d说教痕迹重户外仍想摘花。`r`n2.约30%幼儿浇水过多导致植物烂根。`r`n3.过渡到找春天时认知拓展不够。`r`n解决方法：`r`n1.增设可捡和不能摘分类游戏。`r`n2.种植区增加浇水提示卡。`r`n3.出示燕子蝌蚪春雨图片拓展春天概念。"
    } else {
        $tbl.Cell($lr+1,1).Range.Text="中审议时间"; $tbl.Cell($lr+1,2).Range.Text="2025年4月28日u20145月2日（第9周）"
        try{$tbl.Cell($lr+1,1).Shading.BackgroundPatternColor=15132390;$tbl.Cell($lr+1,2).Shading.BackgroundPatternColor=15132390}catch{}
        $tbl.Cell($lr+2,1).Range.Text="主题名称"; $tbl.Cell($lr+2,2).Range.Text="春天里 u2014 主题总结与反思"
        $tbl.Cell($lr+3,1).Range.Text="幼儿在主题中的行为表现"
        $tbl.Cell($lr+3,2).Range.Text="（一）兴趣`r`n1.u201c春游真好玩u201d谈话中幼儿争相分享春天的发现。`r`n2.u201c放风筝u201d绘本后反复翻阅验证自己的猜想。`r`n3.u201c春天的颜色u201d渲染画对颜色扩散反复尝试。`r`n4.u201c小蝌蚪游啊游u201d对生命过程充满好奇。`r`n（二）能力`r`n1.季节认知：约80%能说出至少5个春天信号。`r`n2.语言发展：丰富春季词汇叙述句长增至5-7字。`r`n3.科学探究：对小动物观察兴趣显著增强。`r`n4.艺术表现：尝试渲染画黏土创作等多种手法。"
        $tbl.Cell($lr+4,1).Range.Text="是否有生成活动"; $tbl.Cell($lr+4,2).Range.Text="主题期间共生成：`r`n1.小草标本集花瓣收藏家（小花小草）`r`n2.花园建构护绿卫士（小花小草）`r`n3.我的春游故事自制小书（找春天）`r`n4.春日音乐会主题表演（结题活动）"
        $tbl.Cell($lr+5,1).Range.Text="重新架构的网络图"
        $sh=$tbl.Cell($lr+5,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()}
        $rg=$tbl.Cell($lr+5,2).Range;$rg.Collapse(0)
        $mp3="$tmpDir\spring_e3.png"
        New-MindMap "春天里·主题总结" @(@{Title="小花小草(21)";Groups=@(@{Name="观察感知";Items=@("小花园","春天的草","亲亲小草")},@{Name="语言艺术";Items=@("小草醒来","绿头发","花儿朵朵")})},@{Title="找春天(23)";Groups=@(@{Name="春日体验";Items=@("春天电话","春游","放风筝")},@{Name="科学艺术";Items=@("春天颜色","春雨","小蝌蚪","蜜蜂")})},@{Title="成果";Groups=@(@{Name="评估";Items=@("80%知春信","75%护花草","观察+5分")})}) $mp3
        $doc.InlineShapes.AddPicture($mp3,$false,$true,$rg)
        $tbl.Cell($lr+6,1).Range.Text="问题与解决"
        $tbl.Cell($lr+6,2).Range.Text="问题：`r`n1.主题容量偏大(40活动)，时间紧张。`r`n2.春雨和下雨了内容重叠。`r`n3.蜗牛蝌蚪养护难假期后死亡。`r`n解决方法：`r`n1.下学期精简为30个核心活动。`r`n2.活体饲养增加假期托管机制。`r`n3.举办春天博览会结题展邀请家长参观。"
    }
}

$tbl.Cell(1,1).Range.Text="小四班 主题中审议调整单 — 春天里"
$tbl.Cell(1,1).Range.Font.Name="楷体";$tbl.Cell(1,1).Range.Font.Size=16;$tbl.Cell(1,1).Range.Font.Bold=$true
$doc.Save();$doc.Close()
Write-Output "春天里 done (1 doc, 3 entries)"
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word)|Out-Null
