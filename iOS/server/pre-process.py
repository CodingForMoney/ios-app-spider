#!./python
import json
from app import App_Status,AppSchemeInfo,AppDetailInfo
import xlwings as xw
import requests
import re
import time
import urllib.parse
import urllib
import base64
import pbPlist
import os

load_excel_path = "./input/iOS.xlsx"
output_excel_path = "./output/iOS_result.xlsx"
app_json_file = "./input/app.json"
ARCHIVE_PLIST_PATH = "./output/plist/"

class MException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return value

def load_local_app_info():
    '''
    从  load_excel_path 文件中读取appid信息
    '''
    xapp = xw.App(visible=False,add_book=False)
    wb = xapp.books.open(load_excel_path)
    time.sleep(8)  # 一定要睡上一定时间，否则会出奇怪的报错。。
    sheet = wb.sheets['Sheet1']  
    app_num = len(sheet.range('B2').expand('down').value)
    print(app_num)
    applist = []
    id_dict = {}
    for i in range(app_num):
        app = AppDetailInfo(i + 1)
        appid = sheet.range('B%d' % (i + 2)).value
        if appid == None:
            print("输入excel表格有问题， 该行没有appid ，请检查文件")
        else:
            appid = str(int(appid))
            app.appID = appid
            if  appid in id_dict:
                print("appid 重复 ！！！！ ",appid)
            else:
                id_dict[appid] = str(appid)
                applist.append(app)
    xapp.quit()
    return applist

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
    }

# 从 25pp下载，需要进行一些限制
downloadHeaders = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13E238',
    'Referer': 'http://m.25pp.com/appstore/appDetails/392899425',
    'content-type': 'application/json; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Tunnel-Command': '0xFE008107'
}


def get_base_info_from_itunes(app):
    '''
     使用 itunes lookup接口，查询基础信息
    '''
    itunesURL = 'https://itunes.apple.com/lookup?country=cn&id=' + app.appID
    resp = requests.get(itunesURL,headers=headers)
    if resp.status_code != 200 :
        raise MException("itunes lookup 接口出错  当前appID 为 : " + app.appID)
    info = resp.json()
    info = info['results']
    if len(info) == 0:
        raise MException("当前appstore无法找到该应用 , appid为"  +  app.appID)
    else:
        info = info[0]
    # 应用名称
    app.name = info['trackName']
    # Appstore分类
    genresList = info['genres']
    app.generes = "、".join(genresList)
    # bundleid
    app.bundleID = info['bundleId']
    # companyName 
    app.company_name = info['artistName']
    # app 页面链接， 在iOS打开自动跳转到app store
    app.store_url = info['trackViewUrl']
    # appSize
    appSize = info['fileSizeBytes']
    appSize = int( int(appSize) / 1000000 )
    app.size = str(appSize) + "MB"
    # appversion
    app.version = info['version']
    # 发布时间
    app.release_time = info['releaseDate']
    # 更新时间
    app.update_time = info['currentVersionReleaseDate']
    # 应用描述
    app.description = info['description']


def get_download_url(app):
    '''从pp越狱平台获取下载地址
    '''
    queryURL = 'https://jsondata.25pp.com/jsondata.html'
    queryJson = '{"itemid":'+ app.appID + ',"isJb":2,"dcType":1,"platform":2,"getOfflineId":1}'
    resp = requests.post(queryURL,data = queryJson,headers = downloadHeaders)
    if resp.status_code != 200 :
        print("25pp查找出错，跳过， 当前appID 为 : ", app.appID)
        return
    text = resp.text
    if text.startswith(u'\ufeff'):
        text = text.encode('utf8')[3:].decode('utf8')
    re_json = json.loads(text)
    if "data" not in re_json:
        print("当前返回值异常 ： " , text)
        return
    data = re_json["data"]
    if data == None :
        print("未在25pp上找到应用 %s，请使用其他方式获取!!! " %(app.appID))
        return
    app.download_url = data["down_u"]
    aid = data["aid"]
    ppurl = "https://www.25pp.com/ios/detail_" + str(aid) 
    appHtml = requests.get(ppurl,headers=headers)
    # 先查越狱版本上获取
    appInfo = None
    app_info_text = re.findall('class="btn-install-x" apptype="app"(.*?)data-stat-pos="install"',appHtml.text)
    if(len(app_info_text) != 0):
        appInfo = app_info_text[0]
        # 越狱版本直接获取越狱版本下载地址
        jb_download_url = re.findall('appdownurl="(.*?)"',appInfo,re.S)[0]
        app.download_url = str(base64.b64decode(jb_download_url), encoding = "utf-8")
    if isinstance(app.download_url,str):
        # 检测download_url是否正确
         if re.match("^http.+ipa$", app.download_url) == None:
            print("查找到的URL是错误的 " + app.download_url)
            app.download_url = ""
         else:
            app.can_download = True
    return



def download_and_get_scheme(app):
    '''下载并解析出URLScheme

    '''
    filename = "./input/" + app.appID + ".ipa"
    download_url = app.download_url
    if(os.path.exists(filename) == False):
        #未下载时，下载文件
        r = requests.get(download_url, stream=True)
        print("url   ",download_url)
        download_command = "wget "+ download_url + " -O " + filename
        os.system(download_command)
    time.sleep(1)
    command = "unzip -o -qq " + filename + " -d ./input/" + app.appID
    os.system(command)

    DSStore = './input/' + app.appID + '/Payload/.DS_Store'
    if(os.path.exists(DSStore)):
        os.remove(DSStore)

    payloadLists = os.listdir('./input/' + app.appID + "/Payload/")
    plistPath = './input/' + app.appID + '/Payload/' + payloadLists[0] + '/Info.plist'
    if(os.path.exists(plistPath) == False):
        raise MException("解压出错，该文件无法自动找到Info.plist ,当前APP为 " +  app.name + " appId :" + app.appID + " path :" + plistPath)

    app.schemes = []
    plist = pbPlist.pbPlist.PBPlist(plistPath)
    # 解析成一个dict结构。
    root = plist.root
    if 'CFBundleDisplayName' in root:
        app.display_name = root['CFBundleDisplayName']
    elif 'CFBundleName' in root:
        app.display_name = root['CFBundleName']
    else:
        app.display_name = "傻逼应用"
    if 'CFBundleURLTypes' in root:
        CFBundleURLTypes = root['CFBundleURLTypes']
        url_schemes_list = []
        for CFBundleURLTypes_item in CFBundleURLTypes:
            if 'CFBundleURLSchemes' in CFBundleURLTypes_item:
                url_schemes_list.extend( CFBundleURLTypes_item['CFBundleURLSchemes'])
        app.schemes =  url_schemes_list
    archive_path = ARCHIVE_PLIST_PATH  + app.appID + ".plist"
    os.system("cp "+ plistPath + " " + archive_path )
    del_command = "rm -rf ./input/" +  app.appID
    os.system(del_command)  
    del_command = "rm " +  filename
    os.system(del_command)  
    return


def main():
    '''
    预处理， 处理 excel表格，以获取我们需要格式的数据。 同时尝试通过25pp下载越狱版本。
    '''
    initCommand = "test -d " + ARCHIVE_PLIST_PATH + " || mkdir -p " + ARCHIVE_PLIST_PATH
    os.system(initCommand)

    applist = load_local_app_info() 
    xapp = xw.App(visible=False,add_book=True)
    wb = xapp.books.add()
    time.sleep(3)
    wb.save(output_excel_path)
    time.sleep(5)

    wb = xapp.books.open(output_excel_path)
    time.sleep(3)
    sheet = wb.sheets['sheet1']
    
    AppDetailInfo.write_excel_label(sheet)
    findedList = []
    failedList = []
    for app in applist:
        try:
            get_base_info_from_itunes(app)
            app.write_to_excel(sheet)
            print("先简单收集 第 %d 个应用" % (app.index))
            findedList.append(app)
        except MException as e:
            print('exception occurred at APP : ',app.appID, 'value:', e.value)
            failedList.append(app)
            app.report_failed(sheet,"-AppStore无法找到应用")
            continue
        wb.save()

    applist = findedList
    json_list = []
    for app in applist:
        try:
            print("下载收集 第 %d 个应用 %s" % (app.index,app.bundleID))
            get_download_url(app)
            if app.can_download:
                download_and_get_scheme(app)
            else:
                app_scheme_info = {}
                app_scheme_info["index"] = app.index 
                app_scheme_info["bundleID"] = app.bundleID
                app_scheme_info["store_url"] = app.store_url
                app_scheme_info["status"] = 0
                json_list.append(app_scheme_info)
            app.write_to_excel(sheet)
        except MException as e:
            print('exception occurred at APP : ',app.appID, 'value:', e.value)
            app.report_failed(sheet,"-25pp下载出错")
            continue
        wb.save()
    time.sleep(3)
    xapp.quit()
    json_list_text = json.dumps(json_list,sort_keys=True,indent=4)
    file = open(app_json_file, 'w')
    file.write(json_list_text)
    file.close()


if __name__ == '__main__':
    main()