#!./python
from flask import Flask
from flask import jsonify
from flask import request
import json
from app import App_Status,AppSchemeInfo
import os
import base64
import pbPlist

server = Flask(__name__)



APPLIST_JSON_FILE = "./input/app.json"
ARCHIVE_PLIST_PATH = "./output/plist/"


app_list = []  #全部的列表
waiting_list = []  # 等待中
crawling_list  = []  # 爬取中
failed_list = []  # 失败的
success_list = []  # 成功的 




def load_data():
    ''' 从本地读取要下载的应用信息
    
    '''
    file_object = open(APPLIST_JSON_FILE)
    if file_object:
        all_the_text = file_object.read()
        file_object.close()
    else:
        print("本地配置文件不存在， 请重新配置")
        return 1
    all_app_list = json.loads(all_the_text)
    all_status_list = [waiting_list,crawling_list,failed_list,success_list]
    for app_dict in all_app_list:
        app = AppSchemeInfo(json_dict=app_dict)
        app_list.append(app)
        if app.status == App_Status.CRAWLING:
            app.status = App_Status.NOT_START
        all_status_list[app.status.value].append(app)
    print("本地数据加载完成.")
    return 0



def save_data():
    ''' 每隔一段时间，以及处理完成后，录入数据
    '''
    save_list = []
    global app_list
    for app in app_list:
        save_list.append(app.json_obj())
    save_text = json.dumps(save_list,sort_keys=True,indent=4)
    global APPLIST_JSON_FILE
    fo = open(APPLIST_JSON_FILE, "w")
    fo.write(save_text);
    fo.close()
    return



def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@server.route('/getTasks', methods=['GET'])
def get_task():
    '''
    获取 任务， 由爬虫自己控制数量， 我们暂时这里只处理下发任务和收集数据。 格式为 {last:1,success:true,app:{...}}
    '''
    ret = {}
    global waiting_list
    global success_list
    global app_list
    last = len(waiting_list)
    if last == 0:
        ret["success"] = True
        ret["last"] = 0
    else:
        needTaskNum = request.args.get('taskNum', '0')
        returnNum =  int(needTaskNum)
        if  returnNum > last:
            returnNum = last
        applist = waiting_list[:returnNum]
        waiting_list = waiting_list[returnNum:]
        crawling_list.extend(applist)
        for i in range(returnNum):
            applist[i].status = App_Status.CRAWLING
            applist[i] = applist[i].json_obj()
        ret["applist"] = applist
        ret["success"] = True
        ret["last"] = last - returnNum
        print(applist)
    print("下发任务， 当前剩余任务数量 ： %d" % (last))
    return jsonify(ret)



@server.route('/reportFail', methods=['GET'])
def report_fail():
    global success_list
    global failed_list
    global app_list
    bundleID = request.args.get('bundleID', '')
    print("下载失败 需要人工处理 ： ", bundleID)
    update_app = None
    for app in crawling_list:
        if app.bundleID == bundleID:
            update_app = app
            break
    if update_app == None:
        print("不可能发生这种错误！！！")
    else:
        update_app.status = App_Status.FAILED
        crawling_list.remove(update_app)
        failed_list.append(update_app)
    save_data()
    print("当前进度为 Success :%d Failed: %d / All : %d " % ( len(success_list) ,len(failed_list), len(app_list)))
    if len(success_list) + len(failed_list) == len(app_list):
        print("下载任务全部完成！！！")
        print("下载任务全部完成！！！")
        print("下载任务全部完成！！！")
        print("下载任务全部完成！！！")
        if len(failed_list):
            print("请查看一下 出错任务 : ")
            for app in failed_list:
                print("--------- ",app.bundleID)
            shutdown_server()
            return 'Server shutting down...'
    return jsonify({})


@server.route('/uploadPlist', methods=['POST'])
def upload_plist():
    '''
    客户端上传收集结果
    上传格式  POST {plist:base64(),bundleID:""}
    '''
    global crawling_list
    global success_list
    global ARCHIVE_PLIST_PATH
    global app_list
    global failed_list

    plist_bytes = request.get_data()
    bundleID = request.args.get('bundleID', '')
    print("下载成功，上传plist ： ", bundleID)
    update_app = None
    for app in crawling_list:
        if app.bundleID == bundleID:
            update_app = app
            break
    if update_app == None:
        print("不可能发生这种错误！！！")
    else:
        update_app.status = App_Status.SUCCESS
        crawling_list.remove(update_app)
        success_list.append(update_app)     
        file_path = ARCHIVE_PLIST_PATH  + bundleID + ".plist"
        file = open(file_path,"wb") 
        file.write(plist_bytes)
        file.close()

        # 读取plist中的scheme
        plist = pbPlist.pbPlist.PBPlist(file_path)
        # 解析成一个dict结构。
        root = plist.root
        if 'CFBundleDisplayName' in root:
            update_app.display_name = root['CFBundleDisplayName']
        elif 'CFBundleName' in root:
            update_app.display_name = root['CFBundleName']
        else:
            update_app.display_name = "傻逼应用"
        update_app.schemes = []
        if 'CFBundleURLTypes' in root:
            CFBundleURLTypes = root['CFBundleURLTypes']
            url_schemes_list = []
            for CFBundleURLTypes_item in CFBundleURLTypes:
                if 'CFBundleURLSchemes' in CFBundleURLTypes_item:
                    url_schemes_list.extend( CFBundleURLTypes_item['CFBundleURLSchemes'])
            update_app.schemes =  url_schemes_list

        save_data()

    print("当前进度为 Success :%d Failed: %d / All : %d " % ( len(success_list) ,len(failed_list), len(app_list)))
    if len(success_list) + len(failed_list) == len(app_list):
        print("下载任务全部完成！！！")
        print("下载任务全部完成！！！")
        print("下载任务全部完成！！！")
        print("下载任务全部完成！！！")
        if len(failed_list):
            print("请查看一下 出错任务 : ")
            for app in failed_list:
                print("--------- ",app.bundleID)
            shutdown_server()
            return 'Server shutting down...'
    return jsonify({})


if __name__ == '__main__':
    initCommand = "test -d " + ARCHIVE_PLIST_PATH + " || mkdir -p " + ARCHIVE_PLIST_PATH
    os.system(initCommand)
    load_data()
    print("初始化完成， 当前剩余APP数量为 %d" % (len(waiting_list)))
    server.run(host='0.0.0.0',debug=True)