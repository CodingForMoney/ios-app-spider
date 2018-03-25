# -*-coding:utf8-*-
import requests
import re
import math
import xlwings as xw
import time

# url = 'http://www.wandoujia.com/category/5023_955'
# tag = "借贷"

# url = 'http://www.wandoujia.com/category/5023_627'
# tag = "银行"

# url = 'http://www.wandoujia.com/category/5023_958'
# tag = "理财记账"

# url = 'http://www.wandoujia.com/category/5023_981'
# tag = "投资"

# url = 'http://www.wandoujia.com/category/5023_631'
# tag = "支付"

# url = 'http://www.wandoujia.com/category/5023_628'
# tag = "炒股"

# url = 'http://www.wandoujia.com/category/5023_629'
# tag = "彩票"

url = 'http://www.wandoujia.com/category/5023_1003'
tag = "保险"

excel = time.strftime('%Y%m%d-%H%M%S',time.localtime(time.time())) + tag + ".xlsx"
app=xw.App(visible=True,add_book=False)
wb=app.books.add()
sht = wb.sheets['sheet1']
sht.range('A1').value='序号'
sht.range('B1').value='应用名称'
sht.range('C1').value='应用分类'
sht.range('D1').value='包名'
sht.range('E1').value='公司名称'
sht.range('F1').value='软件大小'
sht.range('G1').value='版本号'
sht.range('H1').value='更新时间'
sht.range('I1').value='APPId'
sht.range('J1').value='应用评论数'
sht.range('K1').value='应用描述'
sht.range('L1').value='下载量'
sht.range('M1').value='好评率'


headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
    }



html = requests.get(url,headers=headers)#获取网页的源代码
htmlText = html.text.replace('\n', '')
pageText = re.search('<div class="pagination">.*<a class="page-item next-page',htmlText,re.S).group()
pageNumList = re.findall('>(\d+)<',pageText,re.S)
count = 1
for each in pageNumList:
    num = int(each)
    if num > count:
        count = num
i = 1 # 计数
for j in range(1, count + 1):
    pageURL = url + '/' + str(j)
    # print('\n 当前页面为 ' + pageURL)
    pageText = requests.get(pageURL,headers=headers).text
    # print(pageText)
    urls = re.findall('<div class="icon-wrap">\s*<a(.*?)</div>', pageText, re.S)
    for each in urls:
        appURLSearch = re.findall('href="(.*?)"',each,re.S)
        if(len(appURLSearch) == 0):
            print(each , "  不可能找不到URL")
            continue
        appURL = appURLSearch[0]
        # appURL = "http://www.wandoujia.com/apps/cn.jiujiudai.H5291D269"
        # 然后获取url中详细信息。
        sht.range('A%d' % (i+1)).value=str(i)
        appHtml = requests.get(appURL,headers=headers)
        appInfo = re.findall('<body data-suffix=""(.*?)data-page="detail"',appHtml.text)[0]
        Appname = re.findall('data-title="(.*?)" data-pn',appInfo)[0]
        sht.range('B%d' % (i+1)).value=Appname
        Package = re.findall('data-pn="(.*?)" data-app-id',appInfo)[0]
        # print('包名：' ,Package )
        sht.range('D%d' % (i+1)).value=Package
        APPId = re.findall('data-app-id="(.*?)" data-app-vid',appInfo)[0]
        # print('APPId: ' ,APPId )
        sht.range('I%d' % (i+1)).value=APPId

        downloadInfo = re.search('<span class="item install">.*</span>',appHtml.text,re.S).group()
        donwloadNumber = re.findall('>(.*?)</i>',downloadInfo)[0]
        # print('下载量：' ,donwloadNumber)
        sht.range('L%d' % (i+1)).value=donwloadNumber
        favorableInfo = re.search('<span class="item love">.*</span>',appHtml.text,re.S).group()
        favorable = re.findall('>(.*?)</i>',favorableInfo)[0]
        # print('好评率 ： ' ,favorable)
        sht.range('M%d' % (i+1)).value=favorable
        scoreInfo = re.search('<div class="comment-area">.*</a>',appHtml.text,re.S).group()
        Score = re.findall('>(.*?)</i>',scoreInfo)[0]
        # print('应用评论数 : ' , Score)
        sht.range('J%d' % (i+1)).value=Score

        dlInfoList = re.search('<dl class="infos-list">.*<ul class="clearfix relative-download">',appHtml.text,re.S).group()
        Company = re.findall('<span class="dev-sites" itemprop="name">(.*?)</span>',dlInfoList)[0]
        # print('公司名称 : ',Company)
        sht.range('E%d' % (i+1)).value=Company
        Category = re.findall('data-track="detail-click-appTag">(.*?)</a>',dlInfoList)
        Category = "、".join(Category)
        # print('应用分类 : ',Category)
        sht.range('C%d' % (i+1)).value=Category
        Appsize = re.findall('<meta itemprop="fileSize" content="(.*?)"/>',dlInfoList)[0]
        # print('软件大小:' ,Appsize )
        sht.range('F%d' % (i+1)).value=Appsize
        UpdateTime = re.findall('<time id="baidu_time" itemprop="datePublished" datetime="(.*?)">',dlInfoList)[0]
        # print('更新时间：' ,UpdateTime )
        sht.range('H%d' % (i+1)).value=UpdateTime
        Versioncode = re.findall('<dd>&nbsp;(.*?)</dd>',dlInfoList)[0]
        # print('版本号：' ,Versioncode )
        sht.range('G%d' % (i+1)).value=Versioncode

        appText = re.findall('<div data-originheight="100" class="con" itemprop="description">(.*?)</div>',appHtml.text,re.S | re.M)
        if(len(appText) == 0):
            appText = ""
        else:
            appText = appText[0]
        sht.range('K%d' % (i+1)).value=appText
        print('收集第 ',i , ' 个应用信息 : ' + Appname)
        i += 1



print('收集完成！')
wb.save(excel)
# wb.close()
app.quit()
