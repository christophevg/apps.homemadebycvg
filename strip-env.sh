#!/bin/bash
# Strip environment variable prefix before launching a command
# Usage: ./strip-env.sh PREFIX -- command [args...]
#
# Example:
#   ./strip-env.sh LETMELEARN_ -- gunicorn -k eventlet myapp:app
#
# This will copy all LETMELEARN_* variables to their unprefixed versions:
#   LETMELEARN_MONGODB_URI -> MONGODB_URI
#   LETMELEARN_SECRET_KEY -> SECRET_KEY

set -e

if [ $# -lt 3 ] || [ "$2" != "--" ]; then
    echo "Usage: $0 PREFIX -- command [args...]" >&2
    echo "Example: $0 LETMELEARN_ -- gunicorn myapp:app" >&2
    exit 1
fi

PREFIX="$1"
shift 2  # Skip PREFIX and --

# Find all environment variables with the prefix and create unprefixed copies
for var in $(env | grep "^${PREFIX}" | cut -d= -f1); do
    # Get the unprefixed name
    UNPREFIXED="${var#$PREFIX}"
    # Get the value
    VALUE="${!var}"
    # Strip surrounding quotes (single or double) if present
    VALUE="${VALUE#\"}"   # Remove leading double quote
    VALUE="${VALUE%\"}"   # Remove trailing double quote
    VALUE="${VALUE#\'}"   # Remove leading single quote
    VALUE="${VALUE%\'}"   # Remove trailing single quote
    # Export the unprefixed version
    export "${UNPREFIXED}=${VALUE}"
done

# Execute the command with the modified environment
exec "$@"
