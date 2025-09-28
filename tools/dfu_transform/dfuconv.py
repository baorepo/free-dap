#!/usr/bin/env python3

import sys, argparse, struct

ORIGIN   = 0x400
LEN_OFF  = 0x10
CRC_OFF  = 0x14

# 生成 CRC32 表 (IEEE 802.3, reflected input/output 同等效果下的实现)
POLY_TABLE = []
for i in range(256):
    c = i
    for _ in range(8):
        if c & 1:
            c = 0xEDB88320 ^ (c >> 1)
        else:
            c >>= 1
    POLY_TABLE.append(c)

def crc32_forward(crc, data: bytes):
    for b in data:
        crc = POLY_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc & 0xFFFFFFFF

# 与原 dx1elf2dfu 相同的 high_lookup 表（逆向计算用）
HIGH_LOOKUP = [
  0,65,195,130,134,199,69,4,77,12,142,207,203,138,8,73,
  154,219,89,24,28,93,223,158,215,150,20,85,81,16,146,211,
  117,52,182,247,243,178,48,113,56,121,251,186,190,255,125,60,
  239,174,44,109,105,40,170,235,162,227,97,32,36,101,231,166,
  234,171,41,104,108,45,175,238,167,230,100,37,33,96,226,163,
  112,49,179,242,246,183,53,116,61,124,254,191,187,250,120,57,
  159,222,92,29,25,88,218,155,210,147,17,80,84,21,151,214,
  5,68,198,135,131,194,64,1,72,9,139,202,206,143,13,76,
  149,212,86,23,19,82,208,145,216,153,27,90,94,31,157,220,
  15,78,204,141,137,200,74,11,66,3,129,192,196,133,7,70,
  224,161,35,98,102,39,165,228,173,236,110,47,43,106,232,169,
  122,59,185,248,252,189,63,126,55,118,244,181,177,240,114,51,
  127,62,188,253,249,184,58,123,50,115,241,176,180,245,119,54,
  229,164,38,103,99,34,160,225,168,233,107,42,46,111,237,172,
  10,75,201,136,140,205,79,14,71,6,132,197,193,128,2,67,
  144,209,83,18,22,87,213,148,221,156,30,95,91,26,152,217]

def reverse_crc32_calc(crc, data: bytes):
    # data 从尾到头处理
    for b in reversed(data):
        high = (crc >> 24) & 0xFF
        crc ^= POLY_TABLE[HIGH_LOOKUP[high]]
        crc = ((crc << 8) & 0xFFFFFFFF) | (HIGH_LOOKUP[high] ^ b)
    return crc & 0xFFFFFFFF

def calc_span(prior_crc, post_crc):
    table = 0
    for _ in range(4):
        table = ((table << 8) | HIGH_LOOKUP[(post_crc >> 24) & 0xFF]) & 0xFFFFFFFF
        post_crc = ((post_crc ^ POLY_TABLE[table & 0xFF]) << 8) & 0xFFFFFFFF
    span = 0
    for _ in range(4):
        byte = (prior_crc ^ table) & 0xFF
        prior_crc = ((prior_crc >> 8) ^ POLY_TABLE[table & 0xFF]) & 0xFFFFFFFF
        span = ((span >> 8) | (byte << 24)) & 0xFFFFFFFF
        table >>= 8
    return span & 0xFFFFFFFF

def parse_hex(path):
    recs = []
    ext_lin = 0
    with open(path) as f:
        for line in f:
            line=line.strip()
            if not line or line[0] != ':':
                continue
            count = int(line[1:3],16)
            addr  = int(line[3:7],16)
            rtype = int(line[7:9],16)
            data  = bytes.fromhex(line[9:9+count*2])
            chk   = int(line[9+count*2:9+count*2+2],16)
            s = count + (addr>>8) + (addr & 0xFF) + rtype + sum(data)
            if ((s + chk) & 0xFF) != 0:
                raise SystemExit('HEX 校验和错误')
            if rtype == 0x00:
                abs_addr = (ext_lin<<16) + addr
                recs.append((abs_addr,data))
            elif rtype == 0x04:
                ext_lin = int.from_bytes(data,'big')
            elif rtype == 0x01:
                break
    return recs

def build_image(records):
    sel = [(a,d) for a,d in records if a >= ORIGIN]
    if not sel:
        raise SystemExit('HEX 中没有 >=0x400 的应用数据')
    max_end = max(a+len(d) for a,d in sel)
    size = max_end - ORIGIN
    if size & 3:
        size = (size + 3) & ~3
    img = bytearray([0xFF]*size)
    for a,d in sel:
        off = a - ORIGIN
        img[off:off+len(d)] = d
    return img

def write_hex(img: bytes, origin, path):
    with open(path,'w') as f:
        # 写扩展线性地址记录（假设 origin < 1MB，保持简单）
        hi = (origin >> 16) & 0xFFFF
        if hi:
            rec = [0x02,0x00,0x00,0x04,(hi>>8)&0xFF,hi&0xFF]
            csum = ((-sum(rec)) & 0xFF)
            f.write(':%02X%04X%02X%04X%02X\n' % (2,0,4,hi,csum))
        addr = 0
        while addr < len(img):
            chunk = img[addr:addr+16]
            rec_len = len(chunk)
            off16 = (origin + addr) & 0xFFFF
            rec_hdr = [rec_len,(off16>>8)&0xFF,off16&0xFF,0x00]
            csum = (-(sum(rec_hdr)+sum(chunk))) & 0xFF
            f.write(':%02X%04X00%s%02X\n' % (rec_len, off16, chunk.hex().upper(), csum))
            addr += rec_len
        f.write(':00000001FF\n')

def make_dfu(img: bytes, path):
    dfu_crc = crc32_forward(0xFFFFFFFF, img)
    suffix = bytearray([
        0xFF,0xFF,      # bcdDevice
        0x03,0x20,      # idProduct 0x2003
        0x09,0x12,      # idVendor  0x1209
        0x00,0x01,      # bcdDFU 1.00
        ord('U'),ord('F'),ord('D'),
        16              # bLength
    ])
    dfu_crc = crc32_forward(dfu_crc, suffix)
    crc_bytes = struct.pack('<I', dfu_crc)
    with open(path,'wb') as f:
        f.write(img)
        f.write(suffix)
        f.write(crc_bytes)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input_hex')
    ap.add_argument('output_hex')
    ap.add_argument('--dfu', help='同时输出 DFU 文件')
    args = ap.parse_args()

    recs = parse_hex(args.input_hex)
    img  = build_image(recs)

    length = len(img)
    img[LEN_OFF:LEN_OFF+4] = struct.pack('<I', length)

    pre_crc  = crc32_forward(0xFFFFFFFF, img[:CRC_OFF])
    post_crc = reverse_crc32_calc(0, img[CRC_OFF+4:])
    span     = calc_span(pre_crc, post_crc)
    img[CRC_OFF:CRC_OFF+4] = struct.pack('<I', span)

    verify = crc32_forward(0xFFFFFFFF, img)
    if verify != 0:
        raise SystemExit(f'内部 CRC residual 非 0: 0x{verify:08X}')

    write_hex(img, ORIGIN, args.output_hex)
    print(f'已生成补丁 HEX: {args.output_hex}  length={length} span=0x{span:08X}')

    if args.dfu:
        make_dfu(img, args.dfu)
        print(f'已生成 DFU: {args.dfu}')

if __name__ == '__main__':
    main()
