"""Reading rabbit fit results correctly.

IMPORTANT -- the "parms" histogram in a rabbit fitresult stores `fitter.x`, the
*internal* parameter vector. With the default `allowNegativeParam=False` a POI mu
is stored there as sqrt(mu) (the transform that keeps mu >= 0). So the value and
error printed by rabbit_print_pulls_and_constraints.py for a POI are

    x = sqrt(mu)        sigma_x = sigma(mu) / (2 sqrt(mu))

and reading them as if they were mu understates the uncertainty by a factor
2*sqrt(mu) -- a factor 2 at mu = 1. Verified against --allowNegativeParam, which
disables the transform: the two agree to 1.000 for all 8 POIs.

Nuisance parameters are stored directly and need no transform.
"""

import numpy as np

from rabbit import io_tools


def read_parameters(path, result=None, sqrt_transform=True):
    """Return {name: (value, error)} for every parameter, POIs converted to mu.

    sqrt_transform: set False if the fit was run with --allowNegativeParam.
    """
    fitresult, meta = io_tools.get_fitresult(path, result=result, meta=True)
    h = fitresult["parms"].get()
    labels = [str(x) for x in np.array(h.axes["parms"])]
    values = np.asarray(h.values(), dtype=float)
    errors = np.sqrt(np.asarray(h.variances(), dtype=float))

    pois = {str(p) for p in np.asarray(meta["pois"]).astype(str)}

    out = {}
    for name, v, e in zip(labels, values, errors):
        if sqrt_transform and name in pois:
            # mu = x^2, sigma_mu = |dmu/dx| sigma_x = 2|x| sigma_x
            out[name] = (float(v * v), float(2.0 * abs(v) * e))
        else:
            out[name] = (float(v), float(e))
    return out


def poi_names(path):
    _, meta = io_tools.get_fitresult(path, meta=True)
    return [str(p) for p in np.asarray(meta["pois"]).astype(str)]


def read_poi(path, name, result=None, sqrt_transform=True):
    return read_parameters(path, result=result, sqrt_transform=sqrt_transform)[name]
