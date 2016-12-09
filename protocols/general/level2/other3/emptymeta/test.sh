#!/bin/bash

set -e

echo 'Standard output'
echo 'Need to print to test'
echo 'Printing is cool'
sleep 3

echo 'Error output' >&2
echo 'Standard'
echo 'Still an error' >&2

echo 0 > LOGS/SUCCESS_CODE

exit 0
