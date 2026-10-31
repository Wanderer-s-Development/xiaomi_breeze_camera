SKIPUNZIP=0

ui_print "- Installing HyperOS Camera for breeze (Redmi 13 5G / POCO M6 Plus 5G)..."
ui_print "- Setting file permissions..."

set_perm_recursive $MODPATH 0 0 0755 0644
set_perm_recursive $MODPATH/system/product/priv-app/MiuiCamera 0 0 0755 0644
set_perm_recursive $MODPATH/system/system_ext/lib64 0 0 0755 0644
set_perm $MODPATH/service.sh 0 0 0755
set_perm $MODPATH/post-fs-data.sh 0 0 0755

ui_print "- Configured device_features for breeze & breeze_in"
ui_print "- Camera permissions and Aux whitelist installed successfully!"
