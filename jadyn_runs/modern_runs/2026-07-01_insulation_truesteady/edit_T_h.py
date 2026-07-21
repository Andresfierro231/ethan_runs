#!/usr/bin/env python3
"""Scale the external-HTC `h` on the 32 passive insulated-wall rcExternalTemperature
patches inside a collated decomposedBlockData T field (OF13). Preserves the binary
block-length framing by recomputing each processor block's declared byte count.

Usage: edit_T_h.py <in_T> <out_T> <factor>
Only patches in TARGETS are scaled. Powered (Q) segments, stubs, cooler/reducer,
and zeroGradient ncc patches are left untouched.
"""
import re, sys

TARGETS = {
 "junction_lower_left","junction_lower_right","junction_upper_right","junction_upper_left",
 "junction_lower_left_left_extension","junction_lower_left_lower_extension",
 "junction_lower_right_right_extension","junction_lower_right_lower_extension",
 "junction_upper_right_right_extension","junction_upper_right_upper_extension",
 "junction_upper_left_upper_extension",
 "pipeleg_lower_01_fitting","pipeleg_lower_02_straight","pipeleg_lower_03_bend",
 "pipeleg_lower_07_bend","pipeleg_lower_08_straight","pipeleg_lower_09_fitting",
 "pipeleg_right_01_lower","pipeleg_right_02_middle","pipeleg_right_03_upper",
 "pipeleg_upper_01_straight","pipeleg_upper_02_bend","pipeleg_upper_03_straight",
 "pipeleg_upper_07_straight","pipeleg_upper_08_bend","pipeleg_upper_09_straight",
 "pipeleg_left_01_upper","pipeleg_left_02_connector","pipeleg_left_03_fitting",
 "pipeleg_left_05_fitting","pipeleg_left_06_connector","pipeleg_left_07_lower",
}

def scale_block(block_bytes, factor, stats):
    """block_bytes: ascii bytes of one processor field block. Scale h for TARGET patches."""
    txt = block_bytes.decode('latin-1')
    # find boundaryField { ... } region
    bf = txt.find('boundaryField')
    if bf < 0:
        return block_bytes  # no boundaryField on this proc block (interior-only)
    head = txt[:bf]
    body = txt[bf:]
    # iterate over patch entries:  "name"\n    {  ... h  uniform VAL; ... }
    # We rewrite h uniform only inside blocks whose patch name is in TARGETS.
    out = []
    i = 0
    pat = re.compile(r'("?)([A-Za-z_][A-Za-z0-9_]*)\1\s*\n\s*\{')
    # Simpler: split on patch-name+brace, track brace depth to find matching close.
    # We scan char by char to find each patch block start.
    def find_patch_blocks(s):
        # returns list of (name, start_brace_idx, end_brace_idx_inclusive)
        res=[]
        for m in re.finditer(r'"?([A-Za-z_][A-Za-z0-9_]*)"?\s*\n\s*\{', s):
            name=m.group(1)
            bstart=s.index('{', m.start())
            depth=0; j=bstart
            while j < len(s):
                if s[j]=='{': depth+=1
                elif s[j]=='}':
                    depth-=1
                    if depth==0: break
                j+=1
            res.append((name, bstart, j))
        return res
    blocks = find_patch_blocks(body)
    new_body = body
    # rewrite from the end backwards to keep indices valid
    for name, bstart, bend in reversed(blocks):
        if name not in TARGETS: continue
        seg = new_body[bstart:bend+1]
        # written form:  h  \n  { type uniform; value X; }  -- scale only the h-block value
        hm = re.search(r'\bh\s*\n?\s*\{\s*type\s+uniform;\s*value\s+([0-9.eE+-]+);\s*\}', seg)
        if not hm:
            continue
        old=float(hm.group(1)); new=old*factor
        stats[name]=(old,new)
        newseg = seg[:hm.start()] + f'h               \n        {{\n            type            uniform;\n            value           {new!r};\n        }}' + seg[hm.end():]
        new_body = new_body[:bstart] + newseg + new_body[bend+1:]
    return (head + new_body).encode('latin-1')

def main():
    inp, outp, factor = sys.argv[1], sys.argv[2], float(sys.argv[3])
    raw = open(inp,'rb').read()
    stats={}
    out = bytearray()
    pos = 0
    # match each "// ProcessorN\n\n<count>\n(" then block of <count> bytes then ")"
    hdr = re.compile(rb'// Processor(\d+)\n\n(\d+)\n\(')
    last = 0
    for m in hdr.finditer(raw):
        # append everything up to and including the '(' but we will rewrite count
        pre_start = m.start()
        out += raw[last:pre_start]
        proc = m.group(1).decode()
        count = int(m.group(2))
        blk_start = m.end()
        block = raw[blk_start:blk_start+count]
        assert raw[blk_start+count:blk_start+count+1]==b')', f"framing mismatch proc {proc}"
        newblock = scale_block(block, factor, stats)
        newcount = len(newblock)
        out += b'// Processor'+proc.encode()+b'\n\n'+str(newcount).encode()+b'\n('
        out += newblock
        last = blk_start+count  # points at ')'
    out += raw[last:]
    open(outp,'wb').write(out)
    print(f"patched {len(stats)} target patches, factor={factor}")
    for k,(o,n) in sorted(stats.items()):
        print(f"  {k}: {o:.4f} -> {n:.4f}")

if __name__=='__main__':
    main()
