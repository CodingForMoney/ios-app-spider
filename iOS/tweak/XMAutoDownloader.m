#import "XMAutoDownloader.h"
#import <AudioToolbox/AudioToolbox.h>
#import "SKUIOfferView.h"
#import "XMDownladTask.h"
#import <CoreGraphics/CoreGraphics.h>
#import <notify.h>

#pragma clang diagnostic push
#pragma clang diagnostic ignored"-Wobjc-method-access"




static const NSInteger MaxConcurrentTaskNum = 5;// 同时并发任务数量限制。
static NSString *const MXDefaultBaseURL = @"http://10.75.114.96:5000"; // 服务器默认地址。


@interface XMAutoDownloader(){
    
}

// APP 当前在前台， 但是可能
@property (nonatomic,assign) BOOL appIsFront;
@property (nonatomic,assign) BOOL appIsActive;

@property (atomic,assign) BOOL block;
@property (atomic,assign) BOOL buying;// 模拟操作 购买APP中。
// 进行中任务
@property (nonatomic,strong) NSMutableArray<XMDownloadTask *> *tasks;
// 需要卸载的任务列表
@property (nonatomic,strong) NSMutableArray *needUninstallAppList;

@property (nonatomic,strong) XMDownloadTask *currentTask;// 当前打开界面下载的任务。
@property (nonatomic,assign) NSInteger currentUnFinished;// 未完成的任务数量.
@property (nonatomic,assign) NSInteger serverRemaining;// 服务器剩余任务数量

@property (nonatomic,strong) NSString *baseURL;//服务器地址。

//当前只支持 9和10.
@property (nonatomic,assign) double systemVersion;

// 最终所有任务完成。
@property (assign,atomic) BOOL finished;

@end

@implementation XMAutoDownloader


+ (instancetype)shareManager {
    static XMAutoDownloader *instance;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        instance = [[XMAutoDownloader alloc] init];
    });
    return instance;
}

- (instancetype)init {
    if (self = [super init]) {
        _tasks = [[NSMutableArray alloc] initWithCapacity:100];
        _currentUnFinished = 0;
        _serverRemaining = 100;
        _block = NO;
        _baseURL = MXDefaultBaseURL;
        _finished = NO;
        _buying = NO;
        _needUninstallAppList = [[NSMutableArray alloc] initWithCapacity:100];
        _systemVersion = [[UIDevice currentDevice].systemVersion doubleValue];
    }
    return self;
}



#pragma mark - set home page
- (void)startAlert {
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(5 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        if (_systemVersion < 9.0 || _systemVersion > 11.0) {
            [self throwError:@"当前只支持 iOS9 和 iOS10 系统 ！！！"];
        }else {
            UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"开启爬虫"
                                                            message:@"设置爬虫控制服务器 ："
                                                           delegate:self
                                                  cancelButtonTitle:@"取消"
                                                  otherButtonTitles:@"爬！！！", nil];
            [alert setAlertViewStyle:UIAlertViewStylePlainTextInput];
            UITextField *textfield = [alert textFieldAtIndex:0];
            textfield.text = [_baseURL copy];
            [alert show];
        }
    });
}

- (void)alertView:(UIAlertView *)alertView clickedButtonAtIndex:(NSInteger)buttonIndex {
    if (buttonIndex != alertView.cancelButtonIndex) {
        _baseURL = [[alertView textFieldAtIndex:0].text copy];
        [self monitorSystemPop];
        [NSThread detachNewThreadSelector:@selector(threadRun) toTarget:self withObject:nil];
    }
}

- (void)threadRun {
    while (self.finished == NO) {
        [self autoCheck];
        [NSThread sleepForTimeInterval:4];
    }
}


#pragma mark - open storePage && fake click && startdownload

- (void)fakeTouchInView:(UIView *)view {
    CGPoint centerPoint = CGPointMake(view.bounds.size.width / 2.0, view.bounds.size.height / 2.0);
    CGPoint point = [view convertPoint:centerPoint toView:[UIApplication sharedApplication].keyWindow];
    NSInteger pointId = [PTFakeMetaTouch fakeTouchId:[PTFakeMetaTouch getAvailablePointId] AtPoint:point withTouchPhase:UITouchPhaseBegan];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        [PTFakeMetaTouch fakeTouchId:pointId AtPoint:point withTouchPhase:UITouchPhaseEnded];
    });
}

// 第一次点击
#define OfferViewState_NeedInit @"buyInitiate"
// 第二次点击，点击后进行安装
#define OfferViewState_CanBuy   @"buy"
// 刷新或者下载中的状态
#define OfferViewState_NeedCheck @""
// 云同步
#define OfferViewState_Download @"download"
// 已下载完成
#define OfferViewState_Finish   @"open"



- (void)checkStoreViewState:(UIViewController *)documentVC remaingTryTime:(NSInteger)time{
    if (time-- < 1) {
        self.buying = NO;
        return;
    }
    // 根据元素属性来判断APP当前状态。
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        if (documentVC.childViewControllers.count > 0) {
            UIViewController *storePage = documentVC.childViewControllers[0];
            SKUIOfferView *offerView = (SKUIOfferView *)[self seachViewIn:storePage.view forClass:@"SKUIOfferView"];
            if (offerView == nil) {
                [self checkStoreViewState:documentVC remaingTryTime:time];
            }else {
                NSString *str = offerView.offerViewStateDescription;
                if ([str isEqualToString:OfferViewState_NeedInit]) {
                    // 初始状态，点击一次。
                    [self fakeTouchInView:(UIView *)offerView];
                    [self checkStoreViewState:documentVC remaingTryTime:6];// 继续递归一次
                }else if ([str isEqualToString:OfferViewState_CanBuy]){
                    [self fakeTouchInView:(UIView *)offerView];
                    _currentTask.state = XMDownloadStateStarted;
                    // 这次点击完成。
                    self.buying = NO;
                }else if ([str isEqualToString:OfferViewState_Download]){
                    [self fakeTouchInView:(UIView *)offerView];
                    _currentTask.state = XMDownloadStateStarted;
                    self.buying = NO;
                }else {
                    // 其他情况下，应该不会存在。
                    self.buying = NO;
                }
            }
        }else {
            [self checkStoreViewState:documentVC remaingTryTime:time];
        }
    });
    
}


- (void)checkiOS9StoreViewState:(UIViewController *)documentVC remaingTryTime:(NSInteger)time{
    if (time-- < 1) {
        self.buying = NO;
        return;
    }
    // 根据元素属性来判断APP当前状态。
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        if (documentVC.childViewControllers.count > 0) {
            UIViewController *storePage = documentVC.childViewControllers[0];
            UIView *btn = (UIView *)[self seachViewIn:storePage.view forClass:@"SKUIItemOfferButton"];
            if (btn == nil) {
                [self checkiOS9StoreViewState:documentVC remaingTryTime:time];
            }else {
                NSString *title = [btn valueForKey:@"title"];
                // 只支持中文与英文
                if ([title isEqualToString:@"获取"] || [title isEqualToString:@"get"]) {
                    [self fakeTouchInView:btn];
                    [self checkiOS9StoreViewState:documentVC remaingTryTime:6];// 继续递归一次
                }else if([title isEqualToString:@"安装"] || [title isEqualToString:@"install"]){
                    [self fakeTouchInView:btn];
                    _currentTask.state = XMDownloadStateStarted;
                    self.buying = NO;
                }else {
                    // 其他情况下，要判断一个云状态。
                    // 转圈和下载状态，都会有子view， 所以通过这个来判断。
                    if(btn.subviews.count == 0) {
                        [self fakeTouchInView:btn];
                        _currentTask.state = XMDownloadStateStarted;
                        self.buying = NO;
                    }else {
                        NSLog(@"XMAutoDownloader 检测云状态失败， 当前子view数量为 %@",@(btn.subviews.count));
                        self.buying = NO;
                    }
                }
            }
        }else {
            [self checkiOS9StoreViewState:documentVC remaingTryTime:time];
        }
    });
    
}


- (void)startDownloadTask:(XMDownloadTask *)task {
    NSLog(@"XMAutoDownloader startDownloadTask %@",task.bundleID);
    self.buying = YES;
    task.failedTime ++;
    [[UIApplication sharedApplication] openURL:task.storeURL];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        UITabBarController *tab = (UITabBarController *)[UIApplication sharedApplication].keyWindow.rootViewController;
        UINavigationController *nav = tab.selectedViewController;
        UIViewController *documentVC = nav.topViewController;
        // 默认检测10秒，10秒内没有加载完成 ，则网络有问题，请检测网络状态。
        _currentTask = task;
        if (_systemVersion > 10.0) {
            [self checkStoreViewState:documentVC remaingTryTime:10];
        }else {
            [self checkiOS9StoreViewState:documentVC remaingTryTime:10];
        }
    });
}





- (UIView *)seachViewIn:(UIView *)view forClass:(NSString *)className {
    // 根据 类名， 寻找view 下面第一个属于该类名的子 view
    UIView *subView = nil;
    for (UIView *v in view.subviews) {
        NSString *subViewClassName = NSStringFromClass([v class]);
        if ([className isEqualToString:subViewClassName]) {
            subView = v;
        }else if(v.subviews.count > 0) {
            subView = [self seachViewIn:v forClass:className];
        }
        if (subView) {
            break;
        }
    }
    return subView;
}

#pragma mark - autoCheck & server communicate

- (void)autoCheck {
    // 下载任务和上传任务。
    // 首先检测当前任务， 是否有新下载完成的，或者需要上传的
    __block BOOL uninstallListChanged = NO;
    for (XMDownloadTask *task in _tasks) {
//        if (task.state == XMDownloadStateStarted || task.state == XMDownloadStateDownloading) {
        [task checkApplicationInstallState];
//        }
    }
    [_tasks enumerateObjectsUsingBlock:^(XMDownloadTask * _Nonnull task, NSUInteger idx, BOOL * _Nonnull stop) {
        if (task.state == XMDownloadStateFinished) {
            // 完成任务上传。
            [self uploadFinishedTask:task];
            [_tasks removeObject:task];
            [_needUninstallAppList addObject:task.bundleID];
            uninstallListChanged = YES;
        }else if (task.state == XMDownloadStateFailed) {
            // 失败任务上传。
            [self uploadFailedTask:task];
            [_tasks removeObject:task];
        }
    }];
    // 发送通知，卸载应用
    if (uninstallListChanged) {
        NSData *data = [NSJSONSerialization dataWithJSONObject:[_needUninstallAppList copy] options:0 error:nil];
        NSError *error;
        [data writeToFile:UNINSTALL_APPLIST_FILE_PATH options:0 error:&error];
        notify_post(UNINSTALL_APP_NOTIFY);
    }
    
    // 如果当前有空闲，则开启新的任务
    if (self.block == NO && self.buying == NO) {
        for (XMDownloadTask *task in _tasks) {
            if (task.state == XMDownloadStateWaiting) {
                [self startDownloadTask:task];
                break;
            }
        }
    }
    _currentUnFinished = _tasks.count;
    if (_serverRemaining > 0 && _currentUnFinished < MaxConcurrentTaskNum) {
        // 则请求后台，获取新的任务。
        [self downloadNewTask];
    }
    
    if (_serverRemaining == 0 && _tasks.count == 0) {
        // 则下载全部完成。
        NSLog(@"XMAutoDownloader 全部下载任务完成！！！！");
        _finished = YES;
        dispatch_async(dispatch_get_main_queue(), ^{
            UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"完成任务"
                                                            message:@"全部下载任务完成！！！！"
                                                           delegate:nil
                                                  cancelButtonTitle:nil
                                                  otherButtonTitles:@"确认", nil];
            [alert show];
            [self alert];
        });
    }
}


- (void)uploadFinishedTask:(XMDownloadTask *)task{
    // 上传任务并删除应用。
    NSLog(@"XMAutoDownloader finish Task : %@",task.bundleID);
    // 获取plist文件
    NSString *bundlePath = task.bundleURL.absoluteString;
    NSString *plistPath = [bundlePath stringByAppendingString:@"/Info.plist"];
    NSURL *plistURL = [NSURL URLWithString:plistPath];
    NSData *data = [NSData dataWithContentsOfURL:plistURL];
    if ([data isKindOfClass:[NSData class]]) {
        NSString *postURL = [NSString stringWithFormat:@"%@/uploadPlist?bundleID=%@",_baseURL,task.bundleID];
        NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:[NSURL URLWithString:postURL]];
        request.HTTPMethod = @"POST";
        [request setValue:@"text/plain;charset=UTF-8" forHTTPHeaderField:@"CONTENT-TYPE"];
        NSURLSessionTask *sessionTask = [[NSURLSession sharedSession] uploadTaskWithRequest:request fromData:data completionHandler:^(NSData * _Nullable data, NSURLResponse * _Nullable response, NSError * _Nullable error) {
            if (error) {
                [self throwError:@"网络异常， 请检测服务器是否开启，或者是否配置正确！！！"];
            }else {
                
            }
        }];
        [sessionTask resume];
    }else {
        NSLog(@"XMAutoDownloader finish task : %@ , cant find plist file at %@",task.bundleID,plistURL);
        [self throwError:[NSString stringWithFormat:@" 上传任务，未获取到指定的InfoPlist文件 %@ ",task.bundleID]];
        [_tasks removeObject:task];
    }

}

- (void)uploadFailedTask:(XMDownloadTask *)task {
    // 上传失败任务，并删除。
    NSLog(@"XMAutoDownloader failed task : %@",task.bundleID);
    NSString *queryURL = [NSString stringWithFormat:@"%@/reportFail?bundleID=%@",_baseURL,task.bundleID];
    [[[NSURLSession sharedSession] dataTaskWithURL:[NSURL URLWithString:queryURL] completionHandler:^(NSData * _Nullable data, NSURLResponse * _Nullable response, NSError * _Nullable error) {
        if (error) {
            [self throwError:@"网络异常， 请检测服务器是否开启，或者是否配置正确！！！"];
        }
        else {
            
        }
    }] resume];
}

- (void)downloadNewTask {
    // 下载新任务。
    NSInteger needTaskNum = MaxConcurrentTaskNum - _currentUnFinished;
    NSString *queryURL = [NSString stringWithFormat:@"%@/getTasks?taskNum=%@",_baseURL,@(needTaskNum)];
    NSURLSessionTask *task = [[NSURLSession sharedSession] dataTaskWithURL:[NSURL URLWithString:queryURL] completionHandler:^(NSData * _Nullable data, NSURLResponse * _Nullable response, NSError * _Nullable error) {
        if (error) {
            [self throwError:@"网络异常， 请检测服务器是否开启，或者是否配置正确！！！"];
        }
        else {
            NSDictionary *json = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
            if (![json isKindOfClass:[NSDictionary class]]) {
                //
            }else {
                NSInteger last = [[json objectForKey:@"last"] integerValue];
                NSArray *taskList = [json objectForKey:@"applist"];

                _serverRemaining = last;
                for (NSDictionary *taskDict in taskList) {
                    XMDownloadTask *task = [XMDownloadTask taskWithbundleID:[taskDict objectForKey:@"bundleID"]
                                                                  storeURL:[taskDict objectForKey:@"store_url"]];
                    [_tasks addObject:task];
                }
            }
        }
    }];
    [task resume];
}


- (void)throwError:(NSString *)error{
    if (self.block) {
        return;
    }
    self.block = YES;
    dispatch_async(dispatch_get_main_queue(), ^{
        UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"出错"
                                                        message:error
                                                       delegate:nil
                                              cancelButtonTitle:nil
                                              otherButtonTitles:@"确认", nil];
        [alert show];
        [self alert];
    });
}



#pragma  mark - monitorSystemPop
- (void)monitorSystemPop {
    _appIsActive = YES;
    _appIsFront = YES;
    // 监控系统弹出，以触发用户手动输入。
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(applicationWillResignActive) name:UIApplicationWillResignActiveNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(applicationDidBecomeActive) name:UIApplicationDidBecomeActiveNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(applicationWillEnterForeground) name:UIApplicationWillEnterForegroundNotification object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(applicationDidEnterBackground) name:UIApplicationDidEnterBackgroundNotification object:nil];
    
}

- (void)alert {
    SystemSoundID soundID = 1000;
    AudioServicesPlaySystemSound(soundID);
    AudioServicesPlaySystemSound(kSystemSoundID_Vibrate);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.3 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        AudioServicesPlaySystemSound(soundID);
    });
}

- (void)applicationWillResignActive {
    _appIsActive = NO;
    self.block = YES;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.5 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        // 如果 一段时间内，应用没有进入后台，我们则认为，是系统弹框了。
        if (_appIsFront && !_appIsActive) {
            [self alert];
        }else{
            self.block = NO;
        }
    });
}

- (void)applicationDidBecomeActive {
    _appIsActive = YES;
    self.block = YES;
}

- (void)applicationWillEnterForeground {
    _appIsFront = YES;
}

- (void)applicationDidEnterBackground {
    _appIsFront = NO;
}
@end



#pragma clang diagnostic pop
