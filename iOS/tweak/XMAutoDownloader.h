#import <UIKit/UIKit.h>
#import "PTFakeMetaTouch.h"


#define  UNINSTALL_APPLIST_FILE_PATH @"/var/mobile/Library/Preferences/XMAutoDownloader_uninstallAppList"
#define  UNINSTALL_APPLIST_FILE_PATH_LOCK @"/var/mobile/Library/Preferences/XMAutoDownloader_uninstallAppList.lock"

#define  UNINSTALL_APP_NOTIFY     "org.lxm.appdownloader/uninstall"

@interface XMAutoDownloader : NSObject


+ (instancetype)shareManager;


/**
   弹出开启任务弹框。
 */
- (void)startAlert;

@end
