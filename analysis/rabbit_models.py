"""Custom rabbit param models for the Vcb fit.

Usage:
    rabbit_fit.py tensor.hdf5 \
        --paramModel Mu \
        --paramModel analysis.rabbit_models.FreeNorm ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF

Mu supplies r for the tt-vcb signal; FreeNorm supplies one unconstrained
normalisation POI per listed background, reproducing the `xsec_<proc> rateParam`
lines of the Combine datacard and the --redefineSignalPOIs xsec_tt* CR fits.
"""

import numpy as np
import tensorflow as tf

from rabbit.param_models.param_model import ParamModel


class FreeNorm(ParamModel):
    """One unconstrained normalisation parameter per listed process."""

    def __init__(
        self, indata, processes, expectSignal=None, allowNegativeParam=False, **kwargs
    ):
        self.indata = indata

        if isinstance(processes, str):
            processes = [processes]
        wanted = [p.encode() if isinstance(p, str) else p for p in processes]

        missing = [p.decode() for p in wanted if p not in self.indata.procs]
        if missing:
            raise ValueError(
                f"FreeNorm: processes {missing} not in tensor processes "
                f"{[p.decode() for p in self.indata.procs]}"
            )

        # index in the order the caller listed them, so param[i] belongs to
        # processes[i] (np.isin would silently reorder)
        self.proc_idxs = np.array(
            [int(np.where(self.indata.procs == p)[0][0]) for p in wanted],
            dtype=np.int64,
        )

        self.npoi = len(wanted)
        self.npou = 0
        self.params = np.array([b"xsec_" + p for p in wanted])

        self.allowNegativeParam = allowNegativeParam
        self.is_linear = self.nparams == 0 or self.allowNegativeParam

        # In a CompositeParamModel every submodel receives the full
        # --expectSignal list, and set_param_default raises on a name it does
        # not own. Keep only our own parameters so that e.g.
        # "--expectSignal tt-vcb 1.5" (owned by Mu) passes through harmlessly.
        if expectSignal is not None:
            mine = {p.decode() for p in self.params}
            expectSignal = [(n, v) for n, v in expectSignal if n in mine] or None

        self.set_param_default(expectSignal, allowNegativeParam)

    @classmethod
    def parse_args(cls, indata, *args, **kwargs):
        """--paramModel analysis.rabbit_models.FreeNorm <proc_0>,<proc_1>,..."""
        if len(args) != 1:
            raise ValueError(
                f"FreeNorm expects exactly 1 argument (comma separated process "
                f"list) but got {len(args)}"
            )
        return cls(indata, args[0].split(","), **kwargs)

    def compute(self, param, full=False):
        rnorm = tf.tensor_scatter_nd_update(
            tf.ones(self.indata.nproc, dtype=self.indata.dtype),
            self.proc_idxs[:, None],
            param,
        )
        return tf.reshape(rnorm, [1, -1])
