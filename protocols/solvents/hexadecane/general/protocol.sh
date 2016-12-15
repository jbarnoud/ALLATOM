#!/bin/bash
set -euo pipefail

gro_unit=${AA_INPUTS}/units/hexadecane.gro
itp_hd=${AA_INPUTS}/martini_v2.2_solvents.itp

echo gro_unit: ${gro_unit}
echo itp_hd: ${itp_hd}

echo gmx: ${GMX}
echo mdrun: ${MDRUN}

ls -R

ls $(dirname ${AA_SUCCESS_CODE})
echo 1 > ${AA_SUCCESS_CODE}

# Build a hexadecane box
#${GMX} insert-molecules -ci ${gro_unit} -box 3 3 3 -
