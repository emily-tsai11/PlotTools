#!/usr/bin/env python3
"""rabbit_text2hdf5 with channel masking.

The upstream converter has no way to mark a channel masked, so a CR-only fit
cannot be built from a Combine card. This adds --mask <regex>, the equivalent of
Combine's `--setParameters rgx{mask_...}=1`, so that the two tools can be
compared on exactly the same model.

    analysis/cardToTensor.py card.txt -o out --outname A
    analysis/cardToTensor.py card.txt -o out --outname B --mask '_SR$'

Note on rateParams: the converter writes them as unconstrained lnN with a 1%
step, so a Combine rateParam value v maps to the rabbit parameter theta as
v = exp(ln(1.01) * theta). analysis/compareCombine.py --rateparam-lnn undoes it.
"""

import argparse
import os
import re

from rabbit import tensorwriter
from rabbit.datacard_converter import DatacardConverter


def install_mask(pattern):
    rx = re.compile(pattern)
    add_channel, add_data = tensorwriter.TensorWriter.add_channel, tensorwriter.TensorWriter.add_data

    def add_channel_masked(self, axes, name=None, masked=False, flow=False):
        if name is not None and rx.search(name):
            masked = True
        return add_channel(self, axes, name, masked, flow)

    def add_data_unmasked(self, h, channel="ch0", variances=None):
        if self.channels[channel]["masked"]:
            return
        return add_data(self, h, channel, variances)

    tensorwriter.TensorWriter.add_channel = add_channel_masked
    tensorwriter.TensorWriter.add_data = add_data_unmasked


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("datacard")
    p.add_argument("-o", "--output", default="./")
    p.add_argument("--outname", default=None)
    p.add_argument("--mask", default=None, help="regex; matching channels become masked")
    p.add_argument("--mass", default="125.38")
    p.add_argument("--symmetrize", default=None,
                   choices=[None, "conservative", "average", "linear", "quadratic"])
    p.add_argument("--sparse", action="store_true")
    args = p.parse_args()

    if args.mask:
        install_mask(args.mask)

    conv = DatacardConverter(args.datacard, mass=args.mass, symmetrize=args.symmetrize)
    writer = conv.convert_to_hdf5(sparse=args.sparse)
    masked = [c for c, v in writer.channels.items() if v["masked"]]
    print(f"masked channels: {masked}")

    name = args.outname or os.path.splitext(os.path.basename(args.datacard))[0]
    os.makedirs(args.output, exist_ok=True)
    writer.write(outfolder=args.output, outfilename=name)
    print(f"wrote {os.path.join(args.output, name + '.hdf5')}")


if __name__ == "__main__":
    main()
