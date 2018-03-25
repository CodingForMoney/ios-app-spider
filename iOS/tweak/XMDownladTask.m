//
//  XMDownladTask.m
//  JustAProject
//
//  Created by 罗贤明 on 2018/1/6.
//  Copyright © 2018年 罗贤明. All rights reserved.
//

#import "XMDownladTask.h"
#import "ALApplicationList.h"
#import <notify.h>
#pragma clang diagnostic push
#pragma clang diagnostic ignored"-Wobjc-method-access"


@protocol XMLSApplicationWorkspace<NSObject>

- (NSArray *)allApplications;

- (NSArray *)allInstalledApplications;

- (bool)uninstallApplication:(id)arg1 withOptions:(id)arg2;

@end

@protocol XMLSApplicationProxy<NSObject>
@property (nonatomic,strong) NSString *applicationIdentifier;
@property (nonatomic, readonly) NSURL *bundleContainerURL;
@property (nonatomic, readonly) NSURL *bundleURL;
@end

@protocol XMMIInstallerClient<NSObject>

+ (id<XMMIInstallerClient>)installerWithProgressBlock:(id)block;

- (BOOL)uninstallIdentifiers:(NSArray *)list withOptions:(id)a completion:(id)b;
@end

#define XM_MAX_FAILED_TIME 5

@interface XMDownloadTask()

@property (nonatomic,strong) id<XMLSApplicationWorkspace> defaultWorkspace;

@property (nonatomic,strong) NSDate *lastCheck;

@end

@implementation XMDownloadTask

+ (XMDownloadTask *)taskWithbundleID:(NSString *)bundleID storeURL:(NSString *)url {
    XMDownloadTask *task = [[XMDownloadTask alloc] init];
    task.bundleID = bundleID;
    task.storeURL = [NSURL URLWithString:url];
    task.state = XMDownloadStateWaiting;
    task.failedTime = 0;
    Class LSApplicationWorkspace = NSClassFromString(@"LSApplicationWorkspace");
    task.defaultWorkspace =  [LSApplicationWorkspace performSelector:NSSelectorFromString(@"defaultWorkspace")];
    return task;
}


// 定时刷新APP下载状态
- (void)checkApplicationInstallState {
    if (_failedTime > XM_MAX_FAILED_TIME) {
        // 超过3次，置为失败 ：
        _state = XMDownloadStateFailed;
        return;
    }
    NSArray *installedApplications;
    [[ALApplicationList sharedApplicationList] applicationsFilteredUsingPredicate:[NSPredicate predicateWithFormat:@"isSystemApplication = FALSE"]
                                                                      onlyVisible:YES
                                                           titleSortedIdentifiers:&installedApplications];
    
    for (NSString *bundleID in installedApplications) {
        if ([bundleID isEqualToString:_bundleID]) {
            _state = XMDownloadStateFinished;
            NSLog(@"XMAutoDownloader 检测到应用已安装 :%@",_bundleID);
            if (!_bundleURL) {
                NSArray *allApplications = [_defaultWorkspace allApplications];
                for (id<XMLSApplicationProxy> app in allApplications) {
                    if ([app.applicationIdentifier isEqualToString:_bundleID]) {
                        _bundleURL = app.bundleURL;
                    }
                }
            }
            return;
        }
    }

    NSArray *allApplications = [_defaultWorkspace allApplications];
    for (id<XMLSApplicationProxy> app in allApplications) {
        if ([app.applicationIdentifier isEqualToString:_bundleID]) {
            // 还需要判断文件是否存在。
            NSString *bundlePath = app.bundleContainerURL.path;
            if([[NSFileManager defaultManager] fileExistsAtPath:bundlePath]) {
                _state = XMDownloadStateDownloading;
                NSLog(@"XMAutoDownloader 检测到应用正在下载中 :%@",_bundleID);
            }
            return;
        }
    }
    if (_state == XMDownloadStateStarted) {
        // 当已经处于开始阶段，但仍未开始下载，则稍后重新下载。
        NSDate *now = [NSDate date];
        if (_lastCheck) {
            if ([now timeIntervalSinceDate:_lastCheck] > 30 ) {
                // 30秒内未开始下载，则重新移动到下载序列中
                _failedTime ++;
                _state = XMDownloadStateWaiting;
                _lastCheck = nil;
            }
        }else {
            _lastCheck = now;
        }
    }
//    NSLog(@"XMAutoDownloader checkApplicationInstallState state %@",@(_state));
}


@end

#pragma clang diagnostic pop
