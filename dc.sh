#!/bin/bash

set -e

DC="docker-compose -f docker-compose.yaml"

CMD="${DC} $@"

echo "Executing: ${CMD}"
exec ${CMD}
