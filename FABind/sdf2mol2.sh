#!/bin/bash
cd /mnt/data/posebusters/posebusters_benchmark_set
for dir in */; do
    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"
        cd "$dir"        
        for sdf_file in *.sdf; do
            if [ -f "$sdf_file" ]; then
                mol2_file="${sdf_file%.sdf}.mol2"
                echo "Converting $sdf_file to $mol2_file"
                obabel "$sdf_file" -omol2 -O "$mol2_file"
            fi
        done
        cd ..
    fi
done
echo "Conversion complete."
