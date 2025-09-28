#!/bin/bash
python3 dfuconv.py ../../platform/samd11/make/build/free_dap_d11_bl_1k.hex xiao_samd11_patched.hex --dfu xiao_samd11.dfu

rm xiao_samd11_patched.hex