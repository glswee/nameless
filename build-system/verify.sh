#!/bin/bash

export TELEGRAM_ENV_SET="1"

export DEVELOPMENT_CODE_SIGN_IDENTITY="iPhone Distribution: Digital Fortress LLC (C67CF9S4VU)"
export DISTRIBUTION_CODE_SIGN_IDENTITY="iPhone Distribution: Digital Fortress LLC (C67CF9S4VU)"
export DEVELOPMENT_TEAM="C67CF9S4VU"

export API_ID="31498805"
export API_HASH="929ea1b8a71d19f27f21b8be686510e6"

export BUNDLE_ID="app.nameless.messenger"
export APP_CENTER_ID="0"
export IS_INTERNAL_BUILD="false"
export IS_APPSTORE_BUILD="false"
export APPSTORE_ID="686449807"
export APP_SPECIFIC_URL_SCHEME="tgapp"
export PREMIUM_IAP_PRODUCT_ID="org.telegram.telegramPremium.monthly"

if [ -z "$BUILD_NUMBER" ]; then
        echo "BUILD_NUMBER is not defined"
        exit 1
fi

export DEVELOPMENT_PROVISIONING_PROFILE_APP="match Development app.nameless.messenger"
export DISTRIBUTION_PROVISIONING_PROFILE_APP="match AppStore app.nameless.messenger"
export DEVELOPMENT_PROVISIONING_PROFILE_EXTENSION_SHARE="match Development app.nameless.messenger.Share"
export DISTRIBUTION_PROVISIONING_PROFILE_EXTENSION_SHARE="match AppStore app.nameless.messenger.Share"
export DEVELOPMENT_PROVISIONING_PROFILE_EXTENSION_WIDGET="match Development app.nameless.messenger.Widget"
export DISTRIBUTION_PROVISIONING_PROFILE_EXTENSION_WIDGET="match AppStore app.nameless.messenger.Widget"
export DEVELOPMENT_PROVISIONING_PROFILE_EXTENSION_NOTIFICATIONSERVICE="match Development app.nameless.messenger.NotificationService"
export DISTRIBUTION_PROVISIONING_PROFILE_EXTENSION_NOTIFICATIONSERVICE="match AppStore app.nameless.messenger.NotificationService"
export DEVELOPMENT_PROVISIONING_PROFILE_EXTENSION_NOTIFICATIONCONTENT="match Development app.nameless.messenger.NotificationContent"
export DISTRIBUTION_PROVISIONING_PROFILE_EXTENSION_NOTIFICATIONCONTENT="match AppStore app.nameless.messenger.NotificationContent"
export DEVELOPMENT_PROVISIONING_PROFILE_EXTENSION_INTENTS="match Development app.nameless.messenger.SiriIntents"
export DISTRIBUTION_PROVISIONING_PROFILE_EXTENSION_INTENTS="match AppStore app.nameless.messenger.SiriIntents"
export DEVELOPMENT_PROVISIONING_PROFILE_WATCH_APP="match Development app.nameless.messenger.watchkitapp"
export DISTRIBUTION_PROVISIONING_PROFILE_WATCH_APP="match AppStore app.nameless.messenger.watchkitapp"
export DEVELOPMENT_PROVISIONING_PROFILE_WATCH_EXTENSION="match Development app.nameless.messenger.watchkitapp.watchkitextension"
export DISTRIBUTION_PROVISIONING_PROFILE_WATCH_EXTENSION="match AppStore app.nameless.messenger.watchkitapp.watchkitextension"

BUILDBOX_DIR="buildbox"

export CODESIGNING_PROFILES_VARIANT="appstore"

$@
