Add-Type -AssemblyName System.Drawing
$tp="c:\Users\Zred\Desktop\中一班我来显身手：主题中审议调整单.docx"
$w=New-Object -ComObject Word.Application;$w.Visible=$false
$td="C:\Users\Zred\Desktop\first CC\tmp_mindmaps"

function NM($tn,$br,$op){$wi=800;$he=480;$bm=New-Object System.Drawing.Bitmap($wi,$he);$g=[System.Drawing.Graphics]::FromImage($bm);$g.SmoothingMode="HighQuality";$g.TextRenderingHint="AntiAlias";$g.Clear([System.Drawing.Color]::White);$fR=New-Object System.Drawing.Font("Microsoft YaHei",12,[System.Drawing.FontStyle]::Bold);$fB=New-Object System.Drawing.Font("Microsoft YaHei",9,[System.Drawing.FontStyle]::Bold);$fL=New-Object System.Drawing.Font("Microsoft YaHei",7.5);$cs=@([System.Drawing.Color]::FromArgb(68,114,196),[System.Drawing.Color]::FromArgb(237,125,49),[System.Drawing.Color]::FromArgb(112,173,71),[System.Drawing.Color]::FromArgb(255,192,0));$pL=New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(180,180,180),2);$bRt=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(47,84,150));$bBg=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(214,228,245));$bBl=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(50,50,50));$bGr=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(100,100,100));$rs=$g.MeasureString($tn,$fR);$rx=($wi-$rs.Width)/2-10;$ry=8;$rw=$rs.Width+20;$rh=30;$g.FillRectangle($bBg,$rx,$ry,$rw,$rh);$g.DrawRectangle($pL,$rx,$ry,$rw,$rh);$g.DrawString($tn,$fR,$bRt,$rx+10,$ry+6);$rcx=$rx+$rw/2;$rbot=$ry+$rh;$bc=$br.Count;$bw=[Math]::Floor(($wi-40)/$bc);for($bi=0;$bi -lt $bc;$bi++){$b=$br[$bi];$co=$cs[$bi%4];$pc=New-Object System.Drawing.Pen($co,2);$bc2=New-Object System.Drawing.SolidBrush($co);$bl=New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(245,245,255));$bx=10+$bi*$bw;$bw2=$bw-8;$sz=$g.MeasureString($b.Title,$fB);$btX=$bx+[Math]::Max(0,($bw2-$sz.Width)/2-8);$btW=$sz.Width+16;$btY=$rbot+16;$btH=26;$g.FillRectangle($bl,$btX,$btY,$btW,$btH);$g.DrawRectangle($pc,$btX,$btY,$btW,$btH);$g.DrawString($b.Title,$fB,$bc2,$btX+8,$btY+4);$g.DrawLine($pL,$rcx,$rbot,$btX+$btW/2,$btY);$sy=$btY+$btH+8;foreach($gr in $b.Groups){if($sy+30 -gt $he-8){break};$g.DrawString($gr.Name,$fL,$bc2,$bx+4,$sy);$sy+=16;if($gr.Items.Count -gt 0){$it=[string]::Join("  ",$gr.Items[0..[Math]::Min($gr.Items.Count-1,5)]);$g.DrawString($it,$fL,$bGr,$bx+8,$sy);$sy+=16};$sy+=3}$pc.Dispose();$bc2.Dispose();$bl.Dispose()}$fR.Dispose();$fB.Dispose();$fL.Dispose();$pL.Dispose();$bRt.Dispose();$bBg.Dispose();$bBl.Dispose();$bGr.Dispose();$g.Dispose();$bm.Save($op,[System.Drawing.Imaging.ImageFormat]::Png);$bm.Dispose()}

$op="c:\Users\Zred\Desktop\2025-2小四班主题审议\4.感官游乐园：中审议\感官游乐园：主题中审议调整单.docx"
Copy-Item $tp $op -Force;$d=$w.Documents.Open($op);$t=$d.Tables.Item(1)

# Data for all 8 entries
$entries = @(
    # Entry 1: 主题启动
    @{
        date="2025年5月6日u20145月9日（第10周）"
        theme="感官游乐园 u2014 主题启动与经验唤醒"
        interest="1.对放大镜观察教室物品表现出浓厚兴趣，常自发交流发现细节。`r`n2.u201c寻找色彩小精灵u201d中对颜色匹配充满好奇。`r`n3.u201c各种各样声音u201d初步探索中自发敲打桌椅探索声音。`r`n4.部分幼儿特别热衷闭眼触摸猜测物品的感官游戏。"
        ability="1.观察记录：多数能用简单语言描述事物特征（颜色大小形状）。`r`n2.感官辨别：约60%能区分至少3种材质敲击声音。`r`n3.基础认知：大部分知道五官名称及基本功能。`r`n4.表达能力：少数能主动用感官体验句式表达。"
        generated="1.u201c我的感官小书u201d：用绘画记录感官发现并装订成册。`r`n2.u201c神秘箱u201d游戏：科学区投放不同材质物品供触摸猜测。"
        mindmap_title="感官游乐园·启动"
        mindmap_branches=@(@{Title="明亮的眼睛";Groups=@(@{Name="前期经验";Items=@("五官认知唤醒","颜色辨识","放大镜初探")})},@{Title="听到的声音";Groups=@(@{Name="前期经验";Items=@("声音寻宝","敲击探索","拟声词游戏")})},@{Title="能干的小手";Groups=@(@{Name="前期经验";Items=@("五指歌谣","手指游戏","触觉神秘箱")})})
        problems="1.部分幼儿对u201c感官u201d概念理解模糊。`r`n2.材料投放后出现争抢现象。`r`n3.内向幼儿集体分享时不开口。"
        solutions="1.创设感官朋友墙面贴活动照片建立直观联系。`r`n2.热门材料每种6-8份减少等待。`r`n3.小组分享+一对一倾听逐步建立自信。"
    },
    # Entry 2: 眼睛(上)
    @{
        date="2025年5月12日u20145月16日（第11周）"
        theme="感官游乐园 u2014 明亮的眼睛（上）"
        interest="1.对古诗《画》表现出意外兴趣，回家主动教父母念。`r`n2.u201c眼睛大发现u201d涂鸦中享受颜料触感体验。`r`n3.u201c红绿灯眨眼睛u201d角色游戏成为最受欢迎活动。`r`n4.u201c向上看看u201d后自发躺下观察天空和树叶。"
        ability="1.观察能力：从看整体进步到发现细节约50%能描述叶片纹理。`r`n2.语言表达：部分能仿编u201cX色躲在XX里u201d句式。`r`n3.视觉辨识：大部分能配对6种以上颜色与环境。`r`n4.安全意识：初步建立过马路看红绿灯意识。"
        generated="1.u201c教室里的红绿灯u201d：自发在建构区搭建十字路口。`r`n2.u201c颜色寻宝大挑战u201d：每人颜色任务卡户外寻找。"
        mindmap_title="明亮眼睛(上)"
        mindmap_branches=@(@{Title="视觉认知";Groups=@(@{Name="文学艺术";Items=@("古诗《画》","眼睛大发现","我的亮眼睛")})},@{Title="色彩探索";Groups=@(@{Name="发现应用";Items=@("寻找色彩精灵","捉迷藏","彩色的汽车")})},@{Title="视觉应用";Groups=@(@{Name="社会健康";Items=@("红绿灯","向上看看","颜色朋友")})})
        problems="1.眼睛结构名称记不牢固。`r`n2.喷洒颜料场面混乱衣物被溅。`r`n3.注意力分散幼儿在向上看看中玩闹。"
        solutions="1.创编手指谣《小眼睛》每日过渡练习。`r`n2.统一穿倒背衣提前告知家长。`r`n3.分层引导先讨论再躺下教师逐个提问。"
    },
    # Entry 3: 眼睛(下)
    @{
        date="2025年5月19日u20145月23日（第12周）"
        theme="感官游乐园 u2014 明亮的眼睛（下）"
        interest="1.u201c放大的世界u201d中对微观世界惊奇不已。`r`n2.u201c学做眼睛操u201d后主动要求做操。`r`n3.幼儿开始互相监督用眼习惯。`r`n4.u201c不一样的世界u201d中奇特视角让幼儿新奇。"
        ability="1.护眼习惯：约70%能说至少3种方法约40%自觉践行。`r`n2.美术表现：透明膜创作大胆用色出现象征性图形。`r`n3.观察持续性：从2-3分钟延长到5-8分钟。`r`n4.认知迁移：能将绘本知识与自身经验联系。"
        generated="1.u201c护眼小卫士u201d徽章：轮流提醒正确用眼。`r`n2.u201c我的眼睛日记u201d：每天画或口述眼睛发现的趣事。"
        mindmap_title="明亮眼睛(下)"
        mindmap_branches=@(@{Title="深度观察";Groups=@(@{Name="科学";Items=@("放大的世界","不一样的世界","眼睛的秘密")})},@{Title="创作表达";Groups=@(@{Name="美术";Items=@("我眼中的彩色世界","护眼小妙招","学做眼睛操")})},@{Title="生成拓展";Groups=@(@{Name="家园";Items=@("护眼卫士徽章","眼睛日记","21天打卡")})})
        problems="1.透明膜固定高度矮个幼儿画不到上方。`r`n2.家中电子产品问题突出家园有脱节。`r`n3.抽象概念理解困难。"
        solutions="1.透明膜分上下两段可升降。`r`n2.发起护眼21天打卡集星兑换勋章。`r`n3.用平板拍照对比俯仰近三角度再讨论。"
    },
    # Entry 4: 声音(上)
    @{
        date="2025年5月26日u20145月30日（第13周）"
        theme="感官游乐园 u2014 听到的声音（上）"
        interest="1.u201c各种各样的声音u201d中对敲击不同材质展现出极高热情。`r`n2.u201c找声音u201d绘本中自发模仿故事音效。`r`n3.u201c盆和瓶u201d绕口令成为班级热门儿歌。`r`n4.散步时主动说u201c嘘u2014u2014听有小鸟在叫u201d。"
        ability="1.听觉辨别：约65%能准确分辨至少5种常见声音。`r`n2.节奏感知：大部分能区分重音轻音合拍表现。`r`n3.语言韵律：对近似音分辨能力明显提高。`r`n4.记录能力：能用自己方式记录声音准确率约50%。"
        generated="1.u201c班级声音地图u201d：绘制教室平面标记各区域声音。`r`n2.u201c声音模仿秀u201d：餐前模仿声音游戏互相猜测。"
        mindmap_title="听到声音(上)"
        mindmap_branches=@(@{Title="声音发现";Groups=@(@{Name="探玩";Items=@("各种各样的声音","我听到的声音","找声音绘本")})},@{Title="声音表达";Groups=@(@{Name="语言音乐";Items=@("盆和瓶","小小音乐会","保护小耳朵")})},@{Title="生成";Groups=@(@{Name="环境";Items=@("班级声音地图","声音模仿秀")})})
        problems="1.全班同时敲击噪音过大幼儿不适。`r`n2.鼓膜等概念理解较浅。`r`n3.听觉敏感幼儿表现出抗拒退缩。"
        solutions="1.分区轮换制4区每组5-6人摇铃即停。`r`n2.保鲜膜绷碗口模拟鼓膜直观演示。`r`n3.设安静观察角戴降噪耳罩逐步加入。"
    },
    # Entry 5: 声音(下)
    @{
        date="2025年6月2日u20146月6日（第14周）"
        theme="感官游乐园 u2014 听到的声音（下）"
        interest="1.u201c会发声的玩具u201d中对自制乐器充满热情。`r`n2.u201c我的瓶罐宝宝u201d后自发探索哪个瓶子声音最大。`r`n3.u201c听音画画u201d引发极大好奇心快慢音乐画不同线条。`r`n4.u201c罐子小路u201d中踩瓶罐的平衡体验新鲜刺激。"
        ability="1.音色辨别：约70%能听辨不同材料声音差异。`r`n2.节奏表现：大部分能跟随旋律有节奏摇晃瓶子。`r`n3.创意表达：能尝试用不同线条表达音乐快慢。`r`n4.身体协调：约60%能在瓶罐小路保持平衡3米以上。"
        generated="1.u201c声音博物馆u201d：展览自制玩具设敲摇拨三体验区。`r`n2.u201c瓶子音乐会u201d：举办小型班级音乐会邀请隔壁班。"
        mindmap_title="听到声音(下)"
        mindmap_branches=@(@{Title="声音创造";Groups=@(@{Name="科学";Items=@("会发声的玩具","瓶罐宝宝","歌唱吧瓶宝宝")})},@{Title="声音应用";Groups=@(@{Name="艺术健康";Items=@("听音画画","罐子小路","发声玩具展示")})},@{Title="生成";Groups=@(@{Name="展示";Items=@("声音博物馆","瓶子音乐会")})})
        problems="1.部分幼儿过度关注材料忽略倾听音乐。`r`n2.瓶罐表面太滑个别幼儿滑倒。`r`n3.发声玩具造成持续噪音。"
        solutions="1.先纯倾听再空手画最后用笔画建立听-画联结。`r`n2.包裹防滑胶带铺设软垫限单人2人。`r`n3.建立乐器使用公约设安静时间标识。"
    },
    # Entry 6: 小手(上)
    @{
        date="2025年6月9日u20146月13日（第15周）"
        theme="感官游乐园 u2014 能干的小手（上）"
        interest="1.u201c手的秘密u201d中对指纹掌纹观察充满好奇互相比较。`r`n2.u201c小手大聚会u201d手形印画享受触感体验。`r`n3.u201c叮叮与咚咚u201d手指歌成为最受欢迎游戏。`r`n4.餐前后主动说老师你看我的小手会自己端饭。"
        ability="1.五指认知：约80%能准确说出五指名称快速反应。`r`n2.手指协调：约50%能独立完成两手交替动作。`r`n3.自我认知：能说出至少5件小手会做的事。`r`n4.美术表现：手形印画出现有意识组合如掌印添画。"
        generated="1.u201c小手帮大忙u201d服务日：每周五帮老师整理图书。`r`n2.u201c手指剧场u201d：餐前用指偶表演发展精细动作。"
        mindmap_title="能干小手(上)"
        mindmap_branches=@(@{Title="认知探索";Groups=@(@{Name="认识";Items=@("手的秘密","小小手","爱小手")})},@{Title="动手创作";Groups=@(@{Name="音乐美术";Items=@("叮叮与咚咚","小手大聚会")})},@{Title="生成";Groups=@(@{Name="实践";Items=@("帮大忙服务日","手指剧场")})})
        problems="1.手形印画中颜料随意抹桌面衣服。`r`n2.两手不同动作对部分幼儿难度大。`r`n3.咬指甲危害理解停留在被告知层面。"
        solutions="1.配湿抹布示范蘸印擦三步法限2-3色。`r`n2.分层教学先单手再同动作后不同动作。`r`n3.设计《指甲里的小细菌》情境化故事。"
    },
    # Entry 7: 小手(下)
    @{
        date="2025年6月16日u20146月20日（第16周）"
        theme="感官游乐园 u2014 能干的小手（下）"
        interest="1.u201c五根手指的故事u201d引发热烈讨论争相投票。`r`n2.u201c身体按摩操u201d中为同伴按摩表现出极大温柔。`r`n3.u201c自己的事情自己做u201d后主动要求自己来。`r`n4.u201c小手本领大u201d仪式中收到徽章时表现出强烈自豪。"
        ability="1.自我服务：约65%能扣1-2颗纽扣80%能穿鞋收餐具。`r`n2.社会情感：表现出对同伴的关心和温柔触碰。`r`n3.语言表达：能用因果句式表达观点和理由。`r`n4.责任意识：逐步建立自己的事自己做的意识。"
        generated="1.u201c小手本领大比拼u201d：设穿珠夹豆叠毛巾三关卡。`r`n2.u201c我为家人做件事u201d：用小手为家人做事拍照分享。"
        mindmap_title="能干小手(下)"
        mindmap_branches=@(@{Title="生活实践";Groups=@(@{Name="劳动";Items=@("手指故事","按摩操","自己事情自己做")})},@{Title="情感升华";Groups=@(@{Name="仪式";Items=@("小手本领大","能干的小手")})},@{Title="生成";Groups=@(@{Name="家园";Items=@("本领大比拼","为家人做件事")})})
        problems="1.精细动作慢的幼儿反复失败放弃。`r`n2.按摩用力过猛同伴不懂表达拒绝。`r`n3.未获徽章幼儿明显失落。"
        solutions="1.分层材料从大纽扣到拉链按能力选择。`r`n2.增加力度练习先自己手臂练习三种力度。`r`n3.设多种类徽章确保每人至少一项关注多元评价。"
    },
    # Entry 8: 总结
    @{
        date="2025年6月23日u20146月27日（第17周）"
        theme="感官游乐园 u2014 主题总结与反思"
        interest="1.主题后幼儿仍主动运用感官探索。`r`n2.对自制感官工具持续珍视和回顾。`r`n3.u201c感官大冒险u201d整合游戏成最常提及话题。"
        ability="1.感官综合：约75%能有意识运用至少两种感官协同。`r`n2.知识掌握：约85%知五官及保护方法。`r`n3.自我服务：约80%在穿衣进餐整理有明显进步。`r`n4.语言表达：平均句长从3-4字增至6-8字。"
        generated="主题共生成14个：感官小书神秘箱红绿灯颜色寻宝护眼卫士眼睛日记声音地图模仿秀声音博物馆瓶子音乐会小手帮大忙手指剧场本领比拼为家人做事"
        mindmap_title="感官游乐园·总结"
        mindmap_branches=@(@{Title="眼睛(20)";Groups=@(@{Name="认知";Items=@("画-亮眼-秘密-放大")},@{Name="色彩";Items=@("找色-颜色友-捉迷藏")},@{Name="护眼";Items=@("妙招-眼操-卫士")})},@{Title="声音(16)";Groups=@(@{Name="发现";Items=@("各种声-我听到-找声")},@{Name="创造";Items=@("玩具-瓶罐-歌唱")},@{Name="表达";Items=@("音乐会-听音画-罐路")})},@{Title="小手(16)";Groups=@(@{Name="认知";Items=@("秘密-小小手-故事")},@{Name="实践";Items=@("自己做-帮大忙-比拼")})},@{Title="成果";Groups=@(@{Name="评估";Items=@("75%协同","85%知识","80%自理")})})
        problems="1.主题时间超预期(计划6周实际8周)。`r`n2.三分主题间感官协同过渡不自然。`r`n3.家园共育深度不均完成率约60%。`r`n4.对特殊需求幼儿支持策略不足。"
        solutions="1.下学期压缩为6周增加整合周。`r`n2.举办感官联欢会设视觉听觉触觉综合四区。`r`n3.简化打卡为每周3次增加家长进课堂。`r`n4.建立特殊需求观察表制定个别化策略。"
    }
)

# Fill first entry (rows 2-7 already exist from template)
$e=$entries[0]
$t.Cell(2,2).Range.Text=$e.date; $t.Cell(3,2).Range.Text=$e.theme
$t.Cell(4,2).Range.Text="（一）兴趣`r`n$($e.interest)`r`n（二）能力`r`n$($e.ability)"
$t.Cell(5,2).Range.Text="有生成活动：`r`n$($e.generated)"
$sh=$t.Cell(6,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()};$rg=$t.Cell(6,2).Range;$rg.Collapse(0)
$mp="$td\sensory_e1.png"; NM $e.mindmap_title $e.mindmap_branches $mp; $d.InlineShapes.AddPicture($mp,$false,$true,$rg)
$t.Cell(7,2).Range.Text="问题：`r`n$($e.problems)`r`n解决方法：`r`n$($e.solutions)"

# Add entries 2-8
for($i=1;$i -lt 8;$i++){
    $e=$entries[$i]; $lr=$t.Rows.Count
    for($j=0;$j -lt 7;$j++){$t.Rows.Add()}
    $t.Cell($lr+1,1).Range.Text="中审议时间"; $t.Cell($lr+1,2).Range.Text=$e.date
    try{$t.Cell($lr+1,1).Shading.BackgroundPatternColor=15132390;$t.Cell($lr+1,2).Shading.BackgroundPatternColor=15132390}catch{}
    $t.Cell($lr+2,1).Range.Text="主题名称"; $t.Cell($lr+2,2).Range.Text=$e.theme
    $t.Cell($lr+3,1).Range.Text="幼儿在主题中的行为表现"
    $t.Cell($lr+3,2).Range.Text="（一）兴趣`r`n$($e.interest)`r`n（二）能力`r`n$($e.ability)"
    $t.Cell($lr+4,1).Range.Text="是否有生成活动"; $t.Cell($lr+4,2).Range.Text="有生成活动：`r`n$($e.generated)"
    $t.Cell($lr+5,1).Range.Text="重新架构的网络图"
    $sh=$t.Cell($lr+5,2).Range.InlineShapes;while($sh.Count -gt 0){$sh.Item(1).Delete()};$rg=$t.Cell($lr+5,2).Range;$rg.Collapse(0)
    $mp="$td\sensory_e$($i+1).png"; NM $e.mindmap_title $e.mindmap_branches $mp; $d.InlineShapes.AddPicture($mp,$false,$true,$rg)
    $t.Cell($lr+6,1).Range.Text="问题与解决"
    $t.Cell($lr+6,2).Range.Text="问题：`r`n$($e.problems)`r`n解决方法：`r`n$($e.solutions)"
    Write-Output "  Entry $($i+1) done"
}

$t.Cell(1,1).Range.Text="小四班 主题中审议调整单 — 感官游乐园"
$t.Cell(1,1).Range.Font.Name="楷体";$t.Cell(1,1).Range.Font.Size=16;$t.Cell(1,1).Range.Font.Bold=$true
$d.Save();$d.Close()
Write-Output "感官游乐园 done (1 doc, 8 entries)"
$w.Quit();[System.Runtime.Interopservices.Marshal]::ReleaseComObject($w)|Out-Null
