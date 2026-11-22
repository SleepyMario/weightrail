# Weightrail Android preview 0.5.0

A small native offline Android application for Android 8.0/API 26 or newer. No native libraries: compatible with ARM64 phones and x86_64 test emulators. It opens a measurement form and local recent history. Weight, blood pressure and resting heart rate are stored in the application's private SQLite database. Re-saving a date updates only supplied measurements. No desktop import, synchronization or graphs yet. Uninstalling may remove local records; export is not implemented in this initial preview.

Build on designated VM 301 with the Android SDK, Java, zip and a persistent private signing key. Set ANDROID_SDK_ROOT, WEIGHTRAIL_ANDROID_KEYSTORE and WEIGHTRAIL_ANDROID_STOREPASS, then run `bash android/build.sh`. Never commit the keystore or its password. Retain the same signing identity for upgrades. Build output is under android/build and must not enter source archives.
