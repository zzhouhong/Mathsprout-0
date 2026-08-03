Add-Type -AssemblyName System.Drawing
$tp="c:\Users\Zred\Desktop\中一班我来显身手：主题中审议调整单.docx"
$w=New-Object -ComObject Word.Application;$w.Visible=$false
$td="C:\Users\Zred\Desktop\first CC\tmp_mindmaps"

function NM($tn,$br,$op){$wi=800;$he=480;$bm=New-Object System.Drawing.Bitmap($wi,$he);$g=[System.Drawing.Graphics]::FromImage($bm);$g.SmoothingMode="HighQuality";$g.TextRenderingHint="AntiAlias";$g.Clear([System.Drawing.Color]::White);$fR=New-Object System.Drawing.Font("Microsoft YaHei",12,[System.Drawing.FontStyle]::Bold);$fB=New-Object System.Drawing.Font("Microsoft YaHei",9,[System.Drawing.FontStyle]::Bold);$fL=New-Object System.Drawing.Font("Microsoft YaHei",7.5);$cs=@([System.Drawing.Color]::FromArgb(68,114,196),[System.Drawing.Color]::FromArgb(237,125,49),[System.Drawing.Color]::FromArgb(112,173,71));$pL=New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(180,180,180),2);$bRt=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(47,84,150));$bBg=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(214,228,245));$bBl=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(50,50,50));$bGr=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(100,100,100));$rs=$g.MeasureString($tn,$fR);$rx=($wi-$rs.Width)/2-10;$ry=8;$rw=$rs.Width+20;$rh=30;$g.FillRectangle($bBg,$rx,$ry,$rw,$rh);$g.DrawRectangle($pL,$rx,$ry,$rw,$rh);$g.DrawString($tn,$fR,$bRt,$rx+10,$ry+6);$rcx=$rx+$rw/2;$rbot=$ry+$rh;$bc=$br.Count;$bw=[Math]::Floor(($wi-40)/$bc);for($bi=0;$bi -lt $bc;$bi++){$b=$br[$bi];$co=$cs[$bi%3];$pc=New-Object System.Drawing.Pen($co,2);$bc2=New-Object System.Drawing.SolidBrush($co);$bl=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(245,245,255));$bx=10+$bi*$bw;$bw2=$bw-8;$sz=$g.MeasureString($b.Title,$fB);$btX=$bx+[Math]::Max(0,($bw2-$sz.Width)/2-8);$btW=$sz.Width+16;$btY=$rbot+16;$btH=26;$g.FillRectangle($bl,$btX,$btY,$btW,$btH);$g.DrawRectangle($pc,$btX,$btY,$btW,$btH);$g.DrawString($b.Title,$fB,$bc2,$btX+8,$btY+4);$g.DrawLine($pL,$rcx,$rbot,$btX+$btW/2,$btY);$sy=$btY+$btH+8;foreach($gr in $b.Groups){if($sy+30 -gt $he-8){break};$g.DrawString($gr.Name,$fL,$bc2,$bx+4,$sy);$sy+=16;if($gr.Items.Count -gt 0){$it=[string]::Join("  ",$gr.Items[0..[Math]::Min($gr.Items.Count-1,5)]);$g.DrawString($it,$fL,$bGr,$bx+8,$sy);$sy+=16};$sy+=3}$pc.Dispose();$bc2.Dispose();$bl.Dispose()}$fR.Dispose();$fB.Dispose();$fL.Dispose();$pL.Dispose();$bRt.Dispose();$bBg.Dispose();$bBl.Dispose();$bGr.Dispose();$g.Dispose();$bm.Save($op,[System.Drawing.Imaging.ImageFormat]::Png);$bm.Dispose()}

# ====== 顽皮一夏 (3 entries) ======
$op="c:\Users\Zred\Desktop\2025-2小四班主题审议\4.顽皮一夏：中审议\顽皮一夏：主题中审议调整单.docx"
Copy-Item $tp $op -Force;$d=$w.Documents.Open($op);$t=$d.Tables.Item(1)

# Entry 1
$t.Cell(2,2).Range.Text="2025年6月8日u20146月19日（第15-16周）"
$t.Cell(3,2).Range.Text="顽皮一夏 u2014 一起来玩水"
$t.Cell(4,2).Range.Text="（一）兴趣`r`n1.u201c下雨了u201d恰逢雨天，幼儿踩水坑接雨水兴奋不愿回教室。`r`n2.u201c小雨滴真淘气u201d后每下雨幼儿自发念诵儿歌。`r`n3.u201c大雨和小雨u201d中用铃鼓表现雨势对比十分投入。`r`n4.u201c巧运水u201d中反复比较哪个工具运水最快。`r`n（二）能力`r`n1.科学探究：约65%能发现u201c有孔不能运水u201d等简单因果关系。`r`n2.音乐表现：大部分能用声音强弱和动作力度区分大小雨。`r`n3.语言韵律：能完整跟念儿歌并配合动作表演。`r`n4.水的特性：约70%初步感知流动性无固定形状等特性。"
$t.Cell(5,2).Range.Text="有生成活动：`r`n1.u201c雨天日记u201d：每次下雨师幼共同记录雨的类型和雨中游戏。`r`n2.u201c接雨水比赛u201d：用不同容器接雨水比较哪种接得多。"
$sh=$t.Cell(6,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()};$rg=$t.Cell(6,2).Range;$rg.Collapse(0)
$mp1="$td\summer_e1.png"
NM "顽皮一夏·玩水(上)" @(@{Title="雨水探索";Groups=@(@{Name="感知";Items=@("下雨了","下雨真好玩","小雨滴","大雨小雨","夏天雷雨")})},@{Title="运水玩水";Groups=@(@{Name="科学";Items=@("巧运水","让水流起来","小猪洒水车","会变魔术水")})},@{Title="生成";Groups=@(@{Name="记录";Items=@("雨天日记","接雨水比赛")})}) $mp1
$d.InlineShapes.AddPicture($mp1,$false,$true,$rg)
$t.Cell(7,2).Range.Text="问题：`r`n1.雨天活动后约30%幼儿袖子或裤脚湿了。`r`n2.沙池排水不畅导致积水影响后续班级。`r`n3.个别幼儿偷喝了加入色素的水。`r`n解决方法：`r`n1.袖口收口裤脚塞雨鞋，活动后立即擦干。`r`n2.每次玩沙后填平水沟整理沙面。`r`n3.明确实验室规则只能看闻摸不能尝。"

# Entries 2-3
for($e=2;$e -le 3;$e++){$lr=$t.Rows.Count;for($i=0;$i -lt 7;$i++){$t.Rows.Add()}
if($e -eq 2){
    $t.Cell($lr+1,1).Range.Text="中审议时间";$t.Cell($lr+1,2).Range.Text="2025年6月22日u20146月27日（第17周）"
    try{$t.Cell($lr+1,1).Shading.BackgroundPatternColor=15132390;$t.Cell($lr+1,2).Shading.BackgroundPatternColor=15132390}catch{}
    $t.Cell($lr+2,1).Range.Text="主题名称";$t.Cell($lr+2,2).Range.Text="顽皮一夏 u2014 玩水/快快凉下来"
    $t.Cell($lr+3,1).Range.Text="幼儿在主题中的行为表现"
    $t.Cell($lr+3,2).Range.Text="（一）兴趣`r`n1.u201c水枪大战u201d成为最受欢迎户外活动体验团队协作。`r`n2.u201c好玩的沙u201d后沙池升级为有情节建构游戏。`r`n3.u201c我是一只小青蛙u201d中捉害虫环节紧张与喜悦对比鲜明。`r`n4.天气渐热幼儿自然讨论怎么让自己凉快。`r`n（二）能力`r`n1.身体协调：奔跑躲闪投掷平衡明显提高。`r`n2.沙水建构：大部分能用工具进行简单沙水合作搭建。`r`n3.讲述能力：能用时间线索讲述游戏过程。`r`n4.数量认知：约60%能正确点数5以内并数物对应。"
    $t.Cell($lr+4,1).Range.Text="是否有生成活动";$t.Cell($lr+4,2).Range.Text="有生成活动：`r`n1.u201c沙池建筑师u201d：组队搭建主题作品互相参观。`r`n2.u201c自制洒水车u201d：废旧矿泉水瓶扎孔制作洒水车。"
    $t.Cell($lr+5,1).Range.Text="重新架构的网络图"
    $sh=$t.Cell($lr+5,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()};$rg=$t.Cell($lr+5,2).Range;$rg.Collapse(0)
    $mp2="$td\summer_e2.png"
    NM "顽皮一夏·玩水(下)" @(@{Title="沙水(完)";Groups=@(@{Name="运动";Items=@("好玩的沙","水枪大战","小青蛙","玩沙包")})},@{Title="水边世界";Groups=@(@{Name="探索";Items=@("快乐小水滴","水里有什么","荷花几月开")})},@{Title="降温(启)";Groups=@(@{Name="感知";Items=@("热乎乎东西","夏天故事","火辣辣夏天")})}) $mp2
    $d.InlineShapes.AddPicture($mp2,$false,$true,$rg)
    $t.Cell($lr+6,1).Range.Text="问题与解决"
    $t.Cell($lr+6,2).Range.Text="问题：`r`n1.个别幼儿不遵守水枪不射脸部规则。`r`n2.幼儿对月份概念理解困难。`r`n3.过渡到降温时天气不够热。`r`n解决方法：`r`n1.签订安全公约按手印违规暂停。`r`n2.简化月份为季节版。`r`n3.灵活调整先推不依赖高温活动。"
} else {
    $t.Cell($lr+1,1).Range.Text="中审议时间";$t.Cell($lr+1,2).Range.Text="2025年6月29日u20147月4日（第18周）"
    try{$t.Cell($lr+1,1).Shading.BackgroundPatternColor=15132390;$t.Cell($lr+1,2).Shading.BackgroundPatternColor=15132390}catch{}
    $t.Cell($lr+2,1).Range.Text="主题名称";$t.Cell($lr+2,2).Range.Text="顽皮一夏 u2014 主题总结与反思"
    $t.Cell($lr+3,1).Range.Text="幼儿在主题中的行为表现"
    $t.Cell($lr+3,2).Range.Text="（一）兴趣`r`n1.u201c太阳爱吃冰淇淋u201d深受喜爱，幼儿自发续编送冰淇淋故事。`r`n2.u201c冰淇淋u201d黏土创作乐此不疲作品琳琅满目。`r`n3.u201c我爱洗澡u201d后幼儿洗澡时自发哼唱。`r`n4.u201c风车转转转u201d引发对风的好奇。`r`n（二）能力`r`n1.夏季常识：约80%能说至少3种变凉快方法。`r`n2.模式认知：能识别复制ABABAABB模式约55%独立延续。`r`n3.艺术表现：作品更有意图性和装饰性。`r`n4.安全意识：能说至少2种防晒方法。"
    $t.Cell($lr+4,1).Range.Text="是否有生成活动";$t.Cell($lr+4,2).Range.Text="主题期间共生成：`r`n1.雨天日记接雨水比赛（玩水阶段）`r`n2.沙池建筑师自制洒水车（玩水阶段）`r`n3.u201c冷饮店u201d角色游戏（降温阶段）`r`n4.u201c夏日清凉展u201d（结题活动）"
    $t.Cell($lr+5,1).Range.Text="重新架构的网络图"
    $sh=$t.Cell($lr+5,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()};$rg=$t.Cell($lr+5,2).Range;$rg.Collapse(0)
    $mp3="$td\summer_e3.png"
    NM "顽皮一夏·总结" @(@{Title="玩水(21)";Groups=@(@{Name="雨水";Items=@("下雨了","真好玩","小雨滴","雷雨")},@{Name="科学";Items=@("巧运水","水流","魔术水")})},@{Title="降温(19)";Groups=@(@{Name="创作";Items=@("冰淇淋","扇子","清凉帽")},@{Name="防暑";Items=@("防晒","快快凉","爱洗澡")})},@{Title="成果";Groups=@(@{Name="评估";Items=@("80%知降温","65%识模式")})}) $mp3
    $d.InlineShapes.AddPicture($mp3,$false,$true,$rg)
    $t.Cell($lr+6,1).Range.Text="问题与解决"
    $t.Cell($lr+6,2).Range.Text="问题：`r`n1.气温变化大部分体验活动效果打折扣。`r`n2.涉及食物但未真实品尝体验感削弱。`r`n3.学期末后半段推进速度偏快。`r`n解决方法：`r`n1.建立天气弹性机制提前查天气安排。`r`n2.组织真实品鉴后再角色游戏。`r`n3.下学期拆分两阶段预留缓冲周。"
}}

$t.Cell(1,1).Range.Text="小四班 主题中审议调整单 — 顽皮一夏"
$t.Cell(1,1).Range.Font.Name="楷体";$t.Cell(1,1).Range.Font.Size=16;$t.Cell(1,1).Range.Font.Bold=$true
$d.Save();$d.Close()
Write-Output "顽皮一夏 done (1 doc, 3 entries)"
$w.Quit();[System.Runtime.Interopservices.Marshal]::ReleaseComObject($w)|Out-Null
