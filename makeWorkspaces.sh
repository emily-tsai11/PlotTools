#!/bin/bash

# folderIn=RiccardoTemplatesNew
# folderIn=Datacards_280426
# folderIn=Datacards_280426_smoothed
# folderIn=Datacards_280426_trial1
# folderIn=Datacards_280426_trial2
# folderIn=Datacards_280426_trial3
# folderIn=Datacards_290426_correctedBnormalization
# folderIn=Datacards_290426_correctedBnormalization_noPeterson
# folderIn=Datacards_290426_correctedBnormalization_noPeterson_inflateFlav
# folderIn=Datacards_040526_fixes
# folderIn=Datacards_070526_ge2bge1c
# folderIn=Datacards_070526_ge2bge1c_fix
# folderIn=Datacards_070526_CRttWcbM0p2m0p8
# folderIn=Datacards_070526_ge2bge1c_fix_smoothed
# folderIn=Datacards_070526_CRttWcbM0p2m0p8_smoothed
# folderIn=Datacards_080526_ge2bge1c_fix_clean
# folderIn=Datacards_100626_ge2bge1c_fix_clean
# folderIn=Datacards_080526_ge2bge1c_fix_clean_pseudoData5FS
# folderIn=Datacards_100626_ge2bge1c_fix_clean_pseudoData5FS
# folderIn=Datacards_100626_ge2bge1c_fix_clean_forJME
# folderIn=Datacards_100626_ge2bge1c_fix_clean_onlySurvivingVeto
# folderIn=Datacards_190826_clean

# folderIn=Datacards_250826_preUnblinding
# folderIn=Datacards_250826_preUnblinding_nonSmoothed
folderIn=Datacards_250826_preUnblinding_noFlavTagSymm


folderIn=${folderIn}_simplified/
# folderIn=${folderIn}_simplified_forGiacomo/
folderIn=${folderIn}/datacards/

declare -a StringArray=("2024")

for year in ${StringArray[@]}; do
	for channel in SL
	do
		echo ${folderIn}/Vcb_${channel}_${year}.txt
		echo ${folderIn}/workspace_Vcb_${channel}_${year}.root
        # text2workspace.py ${folderIn}/ttHcc_${channel}_${year}.txt -o ${folderIn}/workspace_${channel}_${year}.root -m 125.38 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttH_hbb:rate_ttHbb[1.,-10.,10.]' --PO 'map=.*/ttH_hcc:rate_ttHcc[1.,-10.,10.]' --PO 'map=.*/ttZ_zbb:rate_ttZbb[1.,-10.,10.]' --PO 'map=.*/ttZ_zcc:rate_ttZcc[1.,-10.,10.]'
        text2workspace.py ${folderIn}/Vcb_${channel}_${year}.txt -o ${folderIn}/workspace_Vcb_${channel}_${year}.root -m 125.38 -v 0 --channel-masks --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms
        text2workspace.py ${folderIn}/Vcb_${channel}_${year}.txt -o ${folderIn}/workspace_Vcb_${channel}_${year}_classic.root -m 125.38  -v 0 --channel-masks 
        # text2workspace.py ${folderIn}/NewLNN__ttHcc_${channel}_${year}.txt -o ${folderIn}/workspace_${channel}_${year}.root -m 125.38 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttH_hbb:rate_ttHbb[1.,-10.,10.]' --PO 'map=.*/ttH_hcc:rate_ttHcc[1.,-10.,10.]' --PO 'map=.*/ttZ_zbb:rate_ttZbb[1.,-10.,10.]' --PO 'map=.*/ttZ_zcc:rate_ttZcc[1.,-10.,10.]' --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms
	done
done
