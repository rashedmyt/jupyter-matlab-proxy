#!/bin/bash
# Copyright 2025-2026 The MathWorks, Inc.
# Pre-commit hook to replace MathWorks NPM registry URLs with public NPM registry

# Find all package.json, .npmrc, and other relevant files
echo "Executing pre-commit hook: sanitize-npm-registry"
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '(\.json$|yarn\.lock$)')

if [ -z "$FILES" ]; then
    exit 0
fi

for FILE in $FILES; do
    # Skip if file doesn't exist (it may have been deleted)
    [ -f "$FILE" ] || continue

    echo "Sanitizing NPM registry URL in $FILE"

    case "$FILE" in
        *.json)
            # Replace the MathWorks NPM registry URL with the public NPM registry
            sed -i.bak 's|https://.*/artifactory/api/npm/npm-repos/|https://registry.npmjs.org/|g' "$FILE"
            ;;
        */yarn.lock|yarn.lock)
            # Strip __archiveUrl from resolution lines to remove internal registry references
            # Handles both literal ::__archiveUrl= and URL-encoded %3A%3A__archiveUrl=
            sed -i.bak '/^[[:space:]]*resolution: "/ {
              s/::__archiveUrl=[^"]*//g
              s/%3[aA]%3[aA]__archiveUrl=[^#"]*//g
            }' "$FILE"
            ;;
    esac

    # Remove backup file
    rm -f "${FILE}.bak"

    # Stage the modified file
    git add "$FILE"

    echo "Sanitization complete for $FILE"
done

exit 0
