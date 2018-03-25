# -*-coding:utf8-*-
import requests
import re
import math
import xlwings as xw
import time
import urllib.parse


# 通过应用名来爬去数据。
# 

Request_URL = "http://www.wandoujia.com"
Search_APP = ['微信', 'QQ', '支付宝', '优酷', '爱奇艺', '腾讯视频', 'bilibili', '酷狗', '腾讯音乐', 
'虾米', '网易云音乐', '大众点评', '美团', '百度糯米', '美团外卖', '饿了么', '今日头条', '腾讯新闻',
 '网易新闻', '凤凰新闻', '新浪新闻', '微信读书', '知乎', '喜马拉雅', '蜻蜓FM', 'UC浏览器', 'QQ浏览器',
  '搜狗输入法', '百度输入法', '滴滴', 'uber', '携程', '去哪儿', '12306', '艺龙', '微博', '百度贴吧', 
  '知乎', '最右', '淘宝', '天猫', '京东', '亚马逊', '唯品会', '网易严选', '什么值得买', '返利', '小红书',
   '蘑菇街', '密芽', '聚美优品', '每日优鲜', '分期乐', '拼多多', '网易考拉海购', '洋码头', '菠萝蜜', '豌豆公主',
   '寺库', 'toplife', '闲鱼', '转转', '陌陌', '脉脉', '探探','快手', '虎牙', '花椒', '斗鱼', '王者荣耀', '阴阳师',
    '炉石传说', '梦幻西游', '欢乐斗地主', '开心消消乐', '卡牛', '融360', '融之家', '我爱卡', '51信用卡', '轻松借', 
    '借得到', '挖财']


excel = time.strftime('%Y%m%d-%H%M%S',time.localtime(time.time()))  + "_search.xlsx"
excel_app=xw.App(visible=True,add_book=False)
wb=excel_app.books.add()
sht = wb.sheets['sheet1']

index = 65
sht.range('%c1' % (chr(index))).value='序号'
XuhaoIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='SearchName'
SearchNameIndex = chr(index)
index += 1


sht.range('%c1' % (chr(index))).value='应用名称'
YingyongNameIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='应用分类'
CategoryIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='包名'
PackageNameIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='公司名称'
CompanyNameIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='软件大小'
AppSizeIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='版本号'
VersionCodeIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='更新时间'
UpdateTimeIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='APPId'
AppIDIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='应用评论数'
CommentIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='应用描述'
DescribeIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='下载量'
DownloadIndex = chr(index)
index += 1

sht.range('%c1' % (chr(index))).value='好评率'
ScoreIndex = chr(index)
index += 1


headers = {
        'Referer' : 'http://www.wandoujia.com/apps/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
    }


i = 1
for app_name in Search_APP:
    url = Request_URL + "/search?key=" + urllib.parse.quote(app_name) + "&source=apps"
    pre_search = requests.get(url,headers=headers)
    # print(pre_search.text)
    first_app = re.search('<div class="icon-wrap">\s*<a(.*?)</div>', pre_search.text, re.S).group()
    app_url_search = re.findall('href="(.*?)"',first_app,re.S)
    if(len(app_url_search) == 0):
        print(app_names , "  不可能找不到URL")
        continue
    app_url = app_url_search[0]
    # 然后获取url中详细信息。
    sht.range('%c%d' % (XuhaoIndex,i+1)).value=str(i)
    sht.range('%c%d' % (SearchNameIndex,i+1)).value=app_name
    appHtml = requests.get(app_url,headers=headers)
    appInfo = re.findall('data-suffix=""(.*?)data-page="detail"',appHtml.text)[0]
    Appname = re.findall('data-title="(.*?)" data-pn',appInfo)[0]
    sht.range('%c%d' % (YingyongNameIndex,i+1)).value=Appname
    Package = re.findall('data-pn="(.*?)" data-app-id',appInfo)[0]
    # print('包名：' ,Package )
    sht.range('%c%d' % (PackageNameIndex,i+1)).value=Package
    APPId = re.findall('data-app-id="(.*?)" data-app-vid',appInfo)[0]
    # print('APPId: ' ,APPId )
    sht.range('%c%d' % (AppIDIndex,i+1)).value=APPId

    downloadInfo = re.search('<span class="item install">.*</span>',appHtml.text,re.S).group()
    donwloadNumber = re.findall('>(.*?)</i>',downloadInfo)[0]
    # print('下载量：' ,donwloadNumber)
    sht.range('%c%d' % (DownloadIndex,i+1)).value=donwloadNumber
    favorableInfo = re.search('<span class="item love">.*</span>',appHtml.text,re.S).group()
    favorable = re.findall('>(.*?)</i>',favorableInfo)[0]
    # print('好评率 ： ' ,favorable)
    sht.range('%c%d' % (ScoreIndex,i+1)).value=favorable
    scoreInfo = re.search('<div class="comment-area">.*</a>',appHtml.text,re.S).group()
    Score = re.findall('>(.*?)</i>',scoreInfo)[0]
    # print('应用评论数 : ' , Score)
    sht.range('%c%d' % (CommentIndex,i+1)).value=Score

    dlInfoList = re.search('<dl class="infos-list">.*<ul class="clearfix relative-download">',appHtml.text,re.S).group()
    Company = re.findall('<span class="dev-sites" itemprop="name">(.*?)</span>',dlInfoList)[0]
    # print('公司名称 : ',Company)
    sht.range('%c%d' % (CompanyNameIndex,i+1)).value=Company
    Category = re.findall('data-track="detail-click-appTag">(.*?)</a>',dlInfoList)
    Category = "、".join(Category)
    # print('应用分类 : ',Category)
    sht.range('%c%d' % (CategoryIndex,i+1)).value=Category
    Appsize = re.findall('<meta itemprop="fileSize" content="(.*?)"/>',dlInfoList)[0]
    # print('软件大小:' ,Appsize )
    sht.range('%c%d' % (AppSizeIndex,i+1)).value=Appsize
    UpdateTime = re.findall('<time id="baidu_time" itemprop="datePublished" datetime="(.*?)">',dlInfoList)[0]
    # print('更新时间：' ,UpdateTime )
    sht.range('%c%d' % (UpdateTimeIndex,i+1)).value=UpdateTime
    Versioncode = re.findall('<dd>&nbsp;(.*?)</dd>',dlInfoList)[0]
    # print('版本号：' ,Versioncode )
    sht.range('%c%d' % (VersionCodeIndex,i+1)).value=Versioncode

    appText = re.findall('<div data-originheight="100" class="con" itemprop="description">(.*?)</div>',appHtml.text,re.S | re.M)
    if(len(appText) == 0):
        appText = ""
    else:
        appText = appText[0]
    sht.range('%c%d' % (DescribeIndex,i+1)).value=appText
    print('收集第 ',i , ' 个应用信息 : ' + Appname)
    i += 1



print('收集完成！')
wb.save(excel)
# wb.close()
excel_app.quit()
