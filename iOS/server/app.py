#!./python
import json  
from enum import Enum

class App_Status(Enum):
    '''
    App状态枚举
    '''
    NOT_START = 0
    CRAWLING = 1
    FAILED = 2
    SUCCESS = 3



## excel 中的 index
index = 65
index_index = chr(index)
index += 1
name_index = chr(index)
index += 1
generes_index = chr(index)
index += 1
app_id_index = chr(index)
index += 1
bundle_id_index = chr(index)
index += 1
company_index = chr(index)
index += 1
size_index = chr(index)
index += 1
version_index = chr(index)
index += 1
release_time_index = chr(index)
index += 1
update_time_index = chr(index)
index += 1
store_url_index = chr(index)
index += 1
description_index = chr(index)
index += 1
download_url_index = chr(index)
index += 1
display_name_index = chr(index)
index += 1
scheme_list_index = chr(index)
index += 1
target_scheme_index = chr(index)



class AppSchemeInfo:
    '''
    用于 URLScheme 爬虫的app相关信息
    '''
    def __init__(self, json_dict=None):
        if json_dict == None: 
            self.index = 0  # 输出在excel中的序号。       
            self.bundleID = ''  
            self.store_url = ''  # app store URL
            self.status = App_Status.NOT_START  # 状态
        else:
            self.__dict__ = json_dict
            self.status = App_Status(self.status)


    def json_obj(self):
        js = {}
        if  hasattr(self,"schemes"):
            js["schemes"] = self.schemes
        if hasattr(self,"display_name"):
            js['display_name'] = self.display_name
        js['status'] = self.status.value
        js['index'] = self.index
        js['bundleID'] = self.bundleID
        js['store_url'] = self.store_url
        return js

        # 记录到excel中。
    def write_to_excel(self,sheet):
        '''
        最终再次修改excel
        '''
        if self.status == App_Status.FAILED:
            sheet.range('%c%d' % (index_index ,self.index + 1)).value = str(self.index) + "-AppStore下载失败"
            sheet.range('%c%d' % (index_index ,self.index + 1)).color = (255,0,0)
            sheet.range('%c%d' % (name_index ,self.index + 1)).color = (255,0,0)
            sheet.range('%c%d' % (generes_index ,self.index + 1)).color = (255,0,0)
            sheet.range('%c%d' % (app_id_index ,self.index + 1)).color = (255,0,0)
        else:
            sheet.range('%c%d' % (scheme_list_index ,self.index + 1)).value =  json.dumps(self.schemes) 
            if hasattr(self,"display_name"):
                sheet.range('%c%d' % (display_name_index ,self.index + 1)).value = self.display_name


class AppDetailInfo:
    '''
    app的全部详细信息
    '''
    def __init__(self, index):
        self.index = index
        self.download_url = ""
        self.schemes = []
        self.display_name = ""
        self.target_scheme = ""
        self.can_download = False  # 是否可以从25pp进行下载

    def display(self):
        print(self.__dict__)

    # 记录到excel中。
    def write_to_excel(self,sheet):
        sheet.range('%c%d' % (index_index ,self.index + 1)).value = self.index
        sheet.range('%c%d' % (name_index ,self.index + 1)).value = self.name
        sheet.range('%c%d' % (generes_index ,self.index + 1)).value = self.generes
        sheet.range('%c%d' % (app_id_index ,self.index + 1)).value = self.appID
        sheet.range('%c%d' % (bundle_id_index ,self.index + 1)).value = self.bundleID
        sheet.range('%c%d' % (company_index ,self.index + 1)).value = self.company_name
        sheet.range('%c%d' % (size_index ,self.index + 1)).value = self.size
        sheet.range('%c%d' % (version_index ,self.index + 1)).value = self.version
        sheet.range('%c%d' % (release_time_index , self.index + 1)).value = self.release_time
        sheet.range('%c%d' % (update_time_index ,self.index + 1)).value = self.update_time
        sheet.range('%c%d' % (store_url_index ,self.index + 1)).value = self.store_url
        sheet.range('%c%d' % (description_index ,self.index + 1)).value = self.description
        sheet.range('%c%d' % (download_url_index ,self.index + 1)).value = self.download_url
        sheet.range('%c%d' % (scheme_list_index ,self.index + 1)).value =  json.dumps(self.schemes) 
        sheet.range('%c%d' % (display_name_index ,self.index + 1)).value = self.display_name
        sheet.range('%c%d' % (target_scheme_index ,self.index + 1)).value = self.target_scheme

    def report_failed(self,sheet,error):
        sheet.range('%c%d' % (index_index ,self.index + 1)).value = str(self.index) + error
        sheet.range('%c%d' % (index_index ,self.index + 1)).color = (255,0,0)
        sheet.range('%c%d' % (name_index ,self.index + 1)).color = (255,0,0)
        sheet.range('%c%d' % (generes_index ,self.index + 1)).color = (255,0,0)
        sheet.range('%c%d' % (app_id_index ,self.index + 1)).color = (255,0,0)
        sheet.range('%c%d' % (app_id_index ,self.index + 1)).value = self.appID
        sheet.range('%c%d' % (scheme_list_index ,self.index + 1)).value =  json.dumps(self.schemes) 


    @classmethod
    def write_excel_label(cls,sheet):
        sheet.range('%c1' % (index_index)).value = '序号'
        sheet.range('%c1' % (name_index)).value = '应用名称'
        sheet.range('%c1' % (generes_index)).value ='分类'
        sheet.range('%c1' % (app_id_index)).value = 'APPID'
        sheet.range('%c1' % (bundle_id_index)).value = 'BundleID'
        sheet.range('%c1' % (company_index)).value = '公司名称'
        sheet.range('%c1' % (size_index)).value = '应用大小(MB)'
        sheet.range('%c1' % (version_index)).value = '当前版本号'
        sheet.range('%c1' % (release_time_index)).value = '发布时间'
        sheet.range('%c1' % (update_time_index)).value = '更新时间'
        sheet.range('%c1' % (store_url_index)).value = 'appstore链接'
        sheet.range('%c1' % (description_index)).value = '应用描述'
        sheet.range('%c1' % (download_url_index)).value = 'pp下载地址'
        sheet.range('%c1' % (scheme_list_index)).value = 'Scheme列表'
        sheet.range('%c1' % (display_name_index)).value = '应用展示名称'
        sheet.range('%c1' % (target_scheme_index)).value ='目标Scheme'




