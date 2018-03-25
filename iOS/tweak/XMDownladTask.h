//
//  XMDownladTask.h
//  JustAProject
//
//  Created by 罗贤明 on 2018/1/6.
//  Copyright © 2018年 罗贤明. All rights reserved.
//

#import <Foundation/Foundation.h>

typedef NS_ENUM(NSUInteger, XMDownloadState) {
    XMDownloadStateWaiting,
    XMDownloadStateStarted, // 点击下载后为这个状态，
    XMDownloadStateDownloading, // 需要检测到应用已存在，才会更新为 正在下载中
    XMDownloadStateFinished, // 检测应用已下载完成。
    XMDownloadStateFailed, // 通过appstore ，无法找到应用（收集过程中下架，较少情况）, 或者网络异常导致下载失败。
};


/**
  APP下载与检测任务。
 */
@interface XMDownloadTask : NSObject

@property (nonatomic,strong) NSString *bundleID;
@property (nonatomic,strong) NSURL *storeURL;
// 安装路径
@property (nonatomic,strong) NSURL *bundleURL;

@property (nonatomic,assign)  XMDownloadState state;

@property (nonatomic,assign) NSInteger failedTime;

+ (XMDownloadTask *)taskWithbundleID:(NSString *)bundleID storeURL:(NSString *)url;

// 检测当前app 安装的状况
- (void)checkApplicationInstallState;


@end
