# -*-coding:utf8-*-
import requests
import re
import math
import xlwings as xw
import time
import json
import os
import xml.dom.minidom
import base64
import time
from app import App_Status,AppSchemeInfo
from app import scheme_list_index,target_scheme_index

output_excel_path = "./output/iOS_result.xlsx"
app_json_file = "./input/app.json"

# 读取excel 以判断当前设置的  target scheme 是否是全局唯一。
# 使用时， from checkSchemes import checkSchemes

xapp = xw.App(visible=False,add_book=False)
# afterCheck.
def load_app_json_file():
    # 由于第一步的代码写错，所以这里再编写多步执行。
    file_object = open(app_json_file)
    if file_object:
        all_the_text = file_object.read( )
        file_object.close( )
    all_app_list = json.loads(all_the_text)
    
    wb = xapp.books.open(output_excel_path)
    time.sleep(3)
    sheet = wb.sheets['sheet1']
    time.sleep(1)

    for app_dict in all_app_list:
        app = AppSchemeInfo(json_dict=app_dict)
        app.write_to_excel(sheet)
    wb.save()
    time.sleep(5)
    time.sleep(1)


class SchemeInfo:
    # # 序号为 excel 表格中的行号 
    # index = 0
    # schemes_index =''
    # target_index = ''
    # # 当前所在sheet
    # sheet = None
    # # 当无法解决时， 进行标记，以人工解决。
    # cant_resolve = False
    # # 初始化时，自动获取
    # target = ''
    # # set类型。 初始化时自动获取。
    # schemes = None

    def __init__(self, index,sheet):
        self.index = index
        self.schemes_index = scheme_list_index + str(index)
        self.target_index = target_scheme_index + str(index)
        self.sheet = sheet
        schemes = sheet.range(self.schemes_index).value
        self.cant_resolve = False
        schemes = json.loads(schemes)
        if len(schemes) == 0:
            self.cant_resolve = True
        else:
            for scheme in schemes:
                if scheme == "":
                    schemes.remove(scheme)
            self.schemes = set(schemes)
            self.target = schemes[0]

    # 记录到excel中。
    def toExcel(self):
        if self.cant_resolve:
            index = str(int(self.index))
            self.sheet.range("A" + index).color = (255,0,0)
            self.sheet.range("B" + index).color = (255,0,0)
            self.sheet.range("C" + index).color = (255,0,0)
            self.sheet.range("D" + index).color = (255,0,0)
            self.sheet.range("A" + index).value = str(self.index - 1)  + "-无合适Target"
        else:
            self.sheet.range(self.target_index).value = self.target

def checkSchemes(file_name):
    wb=xapp.books.open(file_name)
    time.sleep(3)
    wb.save()
    time.sleep(3)
    
    scheme_info_list = []
    for sheet in wb.sheets:
        app_num = len(sheet.range('A1').expand('down').value) - 1
        for i in range(app_num):
            scheme_info = SchemeInfo(i+2,sheet)
            # 之前出错的任务不做处理
            if sheet.range("A" + str(int(scheme_info.index))).color == (255,0,0):
                continue
            if scheme_info.cant_resolve == True:
                scheme_info.toExcel()
            else:
                scheme_info_list.append(scheme_info)

    target_list = []
    for scheme_info in scheme_info_list:
        scheme_set = set()
        for item in scheme_info_list:
            if item != scheme_info:
                scheme_set.union(item.schemes)
        unique_scheme = list(scheme_info.schemes - scheme_set)
        if len(unique_scheme) > 0:
            scheme_info.target = unique_scheme[0]
            target_list.append(scheme_info.target)
        else:
            scheme_info.cant_resolve = True
        scheme_info.toExcel()
        wb.save()
            
    plist_str = ""
    nsarray_str = ""
    for scheme in target_list:
        plist_str = plist_str + "<string>" + scheme+ "</string>\n"
        nsarray_str = nsarray_str + "@\"" + scheme + "\", "

    json_list_text = json.dumps(target_list)
    file = open("./output/source.json", 'w')
    file.write(json_list_text)
    file.close()

    file = open("./output/Scheme.plist", 'w')
    file.write(plist_str)
    file.close()

    file = open("./output/nsarray.plist", 'w')
    file.write(nsarray_str)
    file.close()
    wb.save()
    xapp.quit()

    time.sleep(2)
   
    return



if __name__ == '__main__':
    load_app_json_file()
    checkSchemes(output_excel_path)