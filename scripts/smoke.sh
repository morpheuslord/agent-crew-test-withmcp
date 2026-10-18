#!/usr/bin/env bash
# End-to-end smoke test of a running stack, through the UI server only (as a browser would):
# register, log in, team, project, task, comment, attachment upload/download, search, CSV export,
# log out. Exits non-zero on the first failure.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:${UI_PORT:-3000}}"
WORK="$(mktemp -d)"
JAR="$WORK/cookies.txt"
trap 'rm -rf "$WORK"' EXIT

RUN_ID="$(date +%s)-$RANDOM"
EMAIL="smoke-$RUN_ID@example.test"
PASSWORD="smoke-password-$RUN_ID"
TITLE="Smoke task $RUN_ID"

step() { printf '==> %s\n' "$*"; }
fail() { printf 'SMOKE FAILED: %s\n' "$*" >&2; exit 1; }

# GET a page (following redirects), store the body, and print the final status code.
get() {
  curl -sS -L -b "$JAR" -c "$JAR" -o "$WORK/body" -w '%{http_code}' "$BASE_URL$1"
}

# The CSRF token embedded in the last page fetched.
csrf() {
  grep -o 'name="_csrf" value="[^"]*"' "$WORK/body" | head -n1 | sed 's/.*value="\([^"]*\)"/\1/'
}

# POST a form (not following redirects); prints "<status> <location>".
post() {
  local path="$1"; shift
  curl -sS -b "$JAR" -c "$JAR" -o "$WORK/post" -D "$WORK/headers" -w '%{http_code}' \
    "$@" "$BASE_URL$path" > "$WORK/status"
  local location
  location="$(grep -i '^location:' "$WORK/headers" | tr -d '\r' | awk '{print $2}' || true)"
  printf '%s %s\n' "$(cat "$WORK/status")" "$location"
}

expect_redirect() {
  local result="$1" pattern="$2" what="$3"
  [[ "$result" =~ ^303\ $pattern$ ]] || fail "$what: expected 303 to $pattern, got '$result'"
}

uuid='[0-9a-f-]{36}'

step "health"
[[ "$(get /healthz)" == 200 ]] || fail "UI /healthz"
[[ "$(get /readyz)" == 200 ]] || fail "UI /readyz (API not ready)"

step "register $EMAIL"
[[ "$(get /register)" == 200 ]] || fail "register page"
token="$(csrf)"
result="$(post /register --data-urlencode "_csrf=$token" --data-urlencode "email=$EMAIL" \
  --data-urlencode "display_name=Smoke Tester" --data-urlencode "password=$PASSWORD" \
  --data-urlencode "password_confirm=$PASSWORD")"
expect_redirect "$result" "/dashboard" "register"

step "log out and log in again"
[[ "$(get /dashboard)" == 200 ]] || fail "dashboard after register"
expect_redirect "$(post /logout --data-urlencode "_csrf=$(csrf)")" "/login" "logout"
[[ "$(get /login)" == 200 ]] || fail "login page"
result="$(post /login --data-urlencode "_csrf=$(csrf)" --data-urlencode "email=$EMAIL" \
  --data-urlencode "password=$PASSWORD" --data-urlencode "next=/dashboard")"
expect_redirect "$result" "/dashboard" "login"

step "create team"
[[ "$(get /dashboard)" == 200 ]] || fail "dashboard"
result="$(post /teams --data-urlencode "_csrf=$(csrf)" --data-urlencode "name=Smoke Team $RUN_ID")"
expect_redirect "$result" "/teams/$uuid" "create team"
team_path="${result#303 }"

step "create project"
[[ "$(get "$team_path")" == 200 ]] || fail "team page"
result="$(post "$team_path/projects" --data-urlencode "_csrf=$(csrf)" \
  --data-urlencode "name=Smoke Project" --data-urlencode "webhook_url=")"
expect_redirect "$result" "/projects/$uuid" "create project"
project_path="${result#303 }"

step "create task"
[[ "$(get "$project_path")" == 200 ]] || fail "project board"
result="$(post "$project_path/tasks" --data-urlencode "_csrf=$(csrf)" \
  --data-urlencode "title=$TITLE" --data-urlencode "description=**Smoke** test" \
  --data-urlencode "status=todo" --data-urlencode "priority=high" \
  --data-urlencode "assignee_id=" --data-urlencode "due_date=" --data-urlencode "labels=smoke")"
expect_redirect "$result" "$project_path" "create task"
[[ "$(get "$project_path")" == 200 ]] || fail "project board after create"
task_path="$(grep -oE "/tasks/$uuid" "$WORK/body" | head -n1)"
[[ -n "$task_path" ]] || fail "new task not on the board"

step "comment"
[[ "$(get "$task_path")" == 200 ]] || fail "task page"
grep -q '<strong>Smoke</strong>' "$WORK/body" || fail "markdown description not rendered"
result="$(post "$task_path/comments" --data-urlencode "_csrf=$(csrf)" \
  --data-urlencode "body=Smoke comment $RUN_ID")"
expect_redirect "$result" "$task_path" "comment"

step "upload attachment"
printf 'smoke attachment %s\n' "$RUN_ID" > "$WORK/upload.txt"
[[ "$(get "$task_path")" == 200 ]] || fail "task page"
grep -q "Smoke comment $RUN_ID" "$WORK/body" || fail "comment not shown"
result="$(post "$task_path/attachments" -F "_csrf=$(csrf)" -F "file=@$WORK/upload.txt;filename=smoke.txt")"
expect_redirect "$result" "$task_path" "upload"

step "download attachment"
[[ "$(get "$task_path")" == 200 ]] || fail "task page after upload"
download_path="$(grep -oE "/attachments/$uuid/download" "$WORK/body" | head -n1)"
[[ -n "$download_path" ]] || fail "attachment link missing"
curl -sS -f -b "$JAR" -D "$WORK/dl-headers" -o "$WORK/download.txt" "$BASE_URL$download_path" \
  || fail "download request"
cmp -s "$WORK/upload.txt" "$WORK/download.txt" || fail "downloaded file differs from upload"
grep -qi '^content-disposition: attachment' "$WORK/dl-headers" || fail "download not an attachment"

step "search"
[[ "$(get "/search?q=$RUN_ID&sort=title&order=asc")" == 200 ]] || fail "search page"
grep -q "$TITLE" "$WORK/body" || fail "task not found by search"

step "CSV export"
curl -sS -f -b "$JAR" -o "$WORK/export.csv" "$BASE_URL$project_path/export.csv" || fail "export request"
head -n1 "$WORK/export.csv" | grep -q '^id,title,status' || fail "CSV header"
grep -q "$TITLE" "$WORK/export.csv" || fail "task missing from CSV"

step "log out"
[[ "$(get /dashboard)" == 200 ]] || fail "dashboard"
expect_redirect "$(post /logout --data-urlencode "_csrf=$(csrf)")" "/login" "logout"
status="$(curl -sS -b "$JAR" -o /dev/null -w '%{http_code}' "$BASE_URL/dashboard")"
[[ "$status" == 303 ]] || fail "dashboard still reachable after logout ($status)"

echo "SMOKE PASSED"
