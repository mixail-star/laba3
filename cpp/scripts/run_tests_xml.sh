#!/usr/bin/env bash
# Собирает проект, запускает три набора тестов с XML-отчётами и делает reports/index.html
set -uo pipefail
cd "$(dirname "$0")/.."
BUILD=build-tests
cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DLAB3_TESTS=ON -DLAB3_BENCH=OFF || exit 1
cmake --build "$BUILD" -j || exit 1
mkdir -p reports
"./$BUILD/tests_gtest"  --gtest_output=xml:reports/gtest.xml  > /dev/null
"./$BUILD/tests_catch2" --reporter junit --out reports/catch2.xml > /dev/null
"./$BUILD/tests_boost"  --report_level=no --log_format=JUNIT --log_sink=reports/boost.xml > /dev/null
python3 scripts/xml_to_html.py reports
status=$?
# открыть в браузере, если возможно
( xdg-open reports/index.html || open reports/index.html ) >/dev/null 2>&1 || true
exit $status
