#import "XMAutoDownloader.h"
#import <objc/runtime.h>
#import <dlfcn.h>
#import <substrate.h>
#import <sys/utsname.h>
#import <notify.h>

%group AppStoreHook
%hook ASAppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    [[XMAutoDownloader shareManager] startAlert];
    return %orig;
}

%end
%end

static void settingsChangedLowerInstall()
{   
    @autoreleasepool {
        static NSMutableArray *uninstalledAPPlist = nil ;
        if(uninstalledAPPlist == nil) {
            uninstalledAPPlist = [[NSMutableArray alloc] init];
        }
        NSData *data= [NSData dataWithContentsOfFile:UNINSTALL_APPLIST_FILE_PATH];
        if(data == nil) {
            NSLog(@"XMAutoDownloader SpringBoard  数据为空，读写文件出错！！！");
            return;
        }
        NSMutableArray *list = [NSJSONSerialization JSONObjectWithData:data options:NSJSONReadingMutableContainers error:nil];
        [list removeObjectsInArray:uninstalledAPPlist];
        [uninstalledAPPlist addObjectsFromArray:[list copy]];
        for (NSString *bundleID in list) {
            dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0) , ^{
                NSBundle *b = [NSBundle bundleWithPath:@"/System/Library/PrivateFrameworks/MobileInstallation.framework"];
                BOOL success = [b load];
                if(success) {
                    Class LSApplicationWorkspace = NSClassFromString(@"LSApplicationWorkspace");
                    id si = [LSApplicationWorkspace valueForKey:@"defaultWorkspace"];
                    SEL selector=NSSelectorFromString(@"uninstallApplication:withOptions:");
                    [si performSelector:selector withObject:bundleID withObject:nil];
                    NSLog(@"XMAutoDownloader SpringBoard 卸载应用 %@",bundleID);
                }
            });
        }
    }
}

%group SpringBoardHook
%hook SpringBoard

- (void)applicationDidFinishLaunching:(id)arg1 {
    %orig;
    CFNotificationCenterAddObserver(CFNotificationCenterGetDarwinNotifyCenter(), NULL, (CFNotificationCallback)settingsChangedLowerInstall,
     CFSTR(UNINSTALL_APP_NOTIFY), NULL, CFNotificationSuspensionBehaviorCoalesce);
}

%end
%end


// 篡改iOS 系统版本号，以安装高版本的app。 TODO ,处理ios 11的 MZCommerce.ConfirmPaymentSheet_message


// extern const char *__progname;
// static __strong NSString* kCurrentiOSVersion;
// static __strong NSString *kTargetiOSVersion = @"/11.1.1";
// static __strong NSString* kUserAgent = @"User-Agent";
// %group itunesstoredHooks
// %hook NSMutableURLRequest
// - (void)setValue:(NSString *)value forHTTPHeaderField:(NSString *)field
// {
//     if(field && value && [field isEqualToString:kUserAgent]) {
//         if([value rangeOfString:kCurrentiOSVersion].location != NSNotFound) {
//             value = [value stringByReplacingOccurrencesOfString:kCurrentiOSVersion withString:kTargetiOSVersion];
//         }
//     }
//     %orig(value, field);
// }
// %end
// %end
// %group installdHooks
// %hook MIBundle
// - (NSString*)minimumOSVersion
// {
//     NSString* ret = %orig;
//     ret = @"2.0";
//     return ret;
// }
// %end
// %end


%ctor
{
    // struct utsname systemInfo;
    // uname(&systemInfo);
    // kCurrentiOSVersion = [NSString stringWithFormat:@"/%@", [[UIDevice currentDevice] systemVersion]];
    // if(strcmp(__progname, "itunesstored") == 0) {
    //    %init(itunesstoredHooks);
    // } else if(strcmp(__progname, "installd") == 0) { 
    //    %init(installdHooks);
    // } else {
        %init(AppStoreHook);
        %init(SpringBoardHook);
    // }
}
