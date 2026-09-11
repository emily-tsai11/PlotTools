#!/usr/bin/env python3
info = {
    'S1': {
      'scale_args': [
      ]
    },
    'S2': {
      'scale_args': [
            r"""--X-nuisance-group-function 'pTrigEff' 'expr::scaleTrigEff("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pBTag' 'expr::scaleBTag(1.0)'""",
            r"""--X-nuisance-group-function 'pBTagLight' 'expr::scaleBTagLight(1.0)'""",
            r"""--X-nuisance-group-function 'pBTagStat' 'expr::scaleBTagStat("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pEleID' 'expr::scaleEleID("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pEleScale' 'expr::scaleEleID("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pMuonID' 'expr::scaleMuonScale("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pMuonScale' 'expr::scaleMuonScale("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pScaleJ' 'expr::scaleScaleJ("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJAbs' 'expr::scaleScaleJAbs("max(0.3,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJFlav' 'expr::scaleScaleJFlav("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJPileup' '1.0'""",
            r"""--X-nuisance-group-function 'pScaleJRel' 'expr::scaleScaleJRel("max(0.2,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJTime' 'expr::scaleScaleJTime("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJMethod' 'expr::scaleScaleJMethod("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pResJ' 'expr::scaleResJ("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleMet' 'expr::scaleScaleMet("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pJetID' 'expr::scaleJetID(1.0)'""",
            r"""--X-nuisance-group-function 'pLumi' 'expr::scaleLumi(1.0)'""",
            # r"""--X-nuisance-group-function 'pOther' 'expr::scaleOther("1/sqrt(@0)",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pSigTheory' '0.5'""",
            # r"""--X-nuisance-group-function 'pSigTheoryPDF' '0.5'""",
            # r"""--X-nuisance-group-function 'pSkgTheory' '0.5'"""
      ]
    },
    'S3': {
      'scale_args': [
            r"""--X-nuisance-group-function 'pTrigEff' 'expr::scaleTrigEff("1/sqrt(@0)",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pBBTag' 'expr::scaleBBTag(1.0)'""",
            # r"""--X-nuisance-group-function 'pBBTag' 'expr::scaleBBTag("max(0.5,1/sqrt(@0))'""",
            # r"""--X-nuisance-group-function 'pBTag' 'expr::scaleBTag(1.0)'""",
            r"""--X-nuisance-group-function 'pBTag' 'expr::scaleBTag("max(0.5,1/sqrt(@0))'""",
            # r"""--X-nuisance-group-function 'pBTagLight' 'expr::scaleBTagLight(1.0)'""",
            r"""--X-nuisance-group-function 'pBTagLight' 'expr::scaleBTagLight("max(0.5,1/sqrt(@0))'""",
            r"""--X-nuisance-group-function 'pBTagStat' 'expr::scaleBTagStat("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pEleID' 'expr::scaleEleID("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pEleScale' 'expr::scaleEleID("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pMuonID' 'expr::scaleMuonScale("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pMuonScale' 'expr::scaleMuonScale("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            # r"""--X-nuisance-group-function 'pScaleJ' 'expr::scaleScaleJ("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJAbs' 'expr::scaleScaleJAbs("max(0.3,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJFlav' 'expr::scaleScaleJFlav("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJPileup' '1.0'""",
            r"""--X-nuisance-group-function 'pScaleJRel' 'expr::scaleScaleJRel("max(0.2,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJTime' 'expr::scaleScaleJTime("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleJMethod' 'expr::scaleScaleJMethod("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pResJ' 'expr::scaleResJ("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pScaleMet' 'expr::scaleScaleMet("max(0.5,1/sqrt(@0))",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pJetID' 'expr::scaleJetID(1.0)'""",
            r"""--X-nuisance-group-function 'pLumi' 'expr::scaleLumi(0.6)'""",
            # r"""--X-nuisance-group-function 'pOther' 'expr::scaleOther("1/sqrt(@0)",lumiscale[1])'""",
            r"""--X-nuisance-group-function 'pSigTheory' 'expr::scaleSigTheory(0.5)'""",
            r"""--X-nuisance-group-function 'pSigTheoryPDF' 'expr::scaleSigTheoryPDF(0.5)'""",
            r"""--X-nuisance-group-function 'pBkgTheory' 'expr::scaleBkgTheory(0.5)'""",
      ]
    }
}

# --X-rescale-nuisance 'pBkgTheory' 0.5

def GetOpts(scenario):
    return ' '.join(info[scenario]['scale_args'])

if __name__ == "__main__":
    import sys

    if sys.argv[2] == '-o':
        print (GetOpts(sys.argv[1]))

