#!/bin/sh
GRADLE_VERSION=8.5
APP_HOME=$( cd "${APP_HOME:-./}" && pwd -P ) || exit
GRADLE_USER_HOME=${GRADLE_USER_HOME:-$HOME/.gradle}
exec "$APP_HOME/gradle/wrapper/gradle-wrapper.jar" "$@"
