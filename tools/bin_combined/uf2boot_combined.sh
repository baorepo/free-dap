#!/bin/bash

bin_files=($(find . -maxdepth 1 -type f -name "*.bin"))

BOOTLOADER_PATH="${bin_files[0]}"

dd if=/dev/zero of=xiao_samd11.bin bs=1 count=$((0x1600))

dd if="$BOOTLOADER_PATH" of=xiao_samd11.bin conv=notrunc

dd if=../../platform/samd11/make/build/free_dap_d11_bl_5k.bin of=xiao_samd11.bin bs=1 seek=$((0x1600)) conv=notrunc

