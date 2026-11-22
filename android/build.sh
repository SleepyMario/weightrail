#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
TOOLS="$(find "$SDK/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
JAR="$(find "$SDK/platforms" -name android.jar | sort -V | tail -1)"
: "${WEIGHTRAIL_ANDROID_KEYSTORE:?Set a persistent private signing keystore path}"
: "${WEIGHTRAIL_ANDROID_STOREPASS:?Set signing password in environment}"
mkdir -p build/classes build/dex
javac -source 8 -target 8 -bootclasspath "$JAR" -d build/classes src/com/sleepymario/weightrail/MainActivity.java
"$TOOLS/d8" --lib "$JAR" --min-api 26 --output build/dex build/classes/com/sleepymario/weightrail/*.class
"$TOOLS/aapt" package -f -M AndroidManifest.xml -I "$JAR" -F build/unsigned.apk
(cd build/dex && zip -q -j ../unsigned.apk classes.dex)
"$TOOLS/zipalign" -f 4 build/unsigned.apk build/aligned.apk
"$TOOLS/apksigner" sign --ks "$WEIGHTRAIL_ANDROID_KEYSTORE" --ks-pass env:WEIGHTRAIL_ANDROID_STOREPASS --ks-key-alias weightrail --out build/weightrail-0.5.0-android.apk build/aligned.apk
"$TOOLS/apksigner" verify --verbose build/weightrail-0.5.0-android.apk
"$TOOLS/aapt" dump badging build/weightrail-0.5.0-android.apk
