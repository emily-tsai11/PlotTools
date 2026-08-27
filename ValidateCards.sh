
# folderIn=RiccardoTemplates
# folderIn=RiccardoTemplatesNew
# folderIn=Datacards_280426
# folderIn=Datacards_280426_smoothed
# folderIn=Datacards_280426_trial1
# folderIn=Datacards_290426_correctedBnormalization
# folderIn=Datacards_290426_correctedBnormalization_noPeterson
# folderIn=Datacards_040526_fixes
# folderIn=Datacards_070526_ge2bge1c
# folderIn=Datacards_070526_ge2bge1c_fix
# folderIn=Datacards_070526_CRttWcbM0p2m0p8
# folderIn=Datacards_070526_ge2bge1c_fix_smoothed
# folderIn=Datacards_070526_CRttWcbM0p2m0p8_smoothed
# folderIn=Datacards_080526_ge2bge1c_fix_clean
# folderIn=Datacards_080526_ge2bge1c_fix_clean_pseudoData5FS
# folderIn=Datacards_100626_ge2bge1c_fix_clean_pseudoData5FS
# folderIn=Datacards_100626_ge2bge1c_fix_clean_forJME
# folderIn=Datacards_100626_ge2bge1c_fix_clean_onlySurvivingVeto
# folderIn=Datacards_190826_clean
# folderIn=Datacards_250826_preUnblinding
# folderIn=Datacards_250826_preUnblinding_nonSmoothed
folderIn=Datacards_250826_preUnblinding_noFlavTagSymm


declare -a StringArray=("2024")

for year in ${StringArray[@]}; do
	for channel in SL
	do
		echo ${folderIn}/Vcb_${channel}_${year}.txt
		echo ValidateDatacards.py ${folderIn}/Vcb_${channel}_${year}.txt --printLevel 0 --mass 125.38 --jsonFile ${folderIn}/validateJson_${year}_${channel}.json ${folderIn}/validateDatacards_${year}_${channel}.txt
        nohup ValidateDatacards.py ${folderIn}/Vcb_${channel}_${year}.txt --printLevel 0 --mass 125.38 --jsonFile ${folderIn}/validateJson_${year}_${channel}.json &> ${folderIn}/validateDatacards_${year}_${channel}.txt &
	done
done
