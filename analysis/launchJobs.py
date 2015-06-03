#! /usr/bin/env python
import os
import glob
import math
from array import array
import sys
import time

import ROOT

############################################
#            Job steering                  #
############################################
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-b', action='store_true', dest='noX', default=False, help='no X11 windows')
parser.add_option('--doTraining', action='store_true', dest='doTraining', default=False, help='training or not')
parser.add_option('--cleaning', action='store_true', dest='cleaning', default=False, help='training or not')
parser.add_option('--makeROCs', action='store_true', dest='makeROCs', default=False, help='training or not')
parser.add_option('-i','--interactive', action='store_true', dest='interactive', default=False, help='training or not')

(options, args) = parser.parse_args()



sampleDir = '/uscms_data/d2/ntran/physics/SUSY/theory/DissectingJetsPlusMET/processFiles/samples/';
# weightDir = '/eos/uscms/store/user/ntran/SUSY/theory_JPM/training/weights';
# plotDir   = '/eos/uscms/store/user/ntran/SUSY/theory_JPM/training/plots';	
weightDir = './weights';
eosweightdir = '/store/user/ntran/SUSY/theory_JPM/training/';
if options.makeROCs and options.interactive: 
	weightDir = '/uscms_data/d2/ntran/physics/SUSY/theory/DissectingJetsPlusMET/analysis/training/weights';
plotDir   = './plots';

def condorize(command,tag):

		print "--------------------"
		print "Processing sample..."

		prefix = "o";
		prefixR = "R";
		if options.makeROCs: prefix = "op";
		if options.makeROCs: prefixR = "opR";

		startdir = os.getcwd();
		#change to a tmp dir
		if not os.path.exists('tmp'): os.makedirs('tmp');
		os.chdir("tmp");
		curdir = os.getcwd();

		f1n = "tmp_%s.sh" %(tag);
		f1=open(f1n, 'w')
		f1.write("#!/bin/sh \n");

		# setup environment
		f1.write("source /cvmfs/cms.cern.ch/cmsset_default.csh \n");
		f1.write("set SCRAM_ARCH=slc6_amd64_gcc481\n")
		f1.write("cd /uscms_data/d2/ntran/physics/SUSY/Run2/combination/CMSSW_7_2_0/src/ \n")
		f1.write("eval `scramv1 runtime -sh`\n")
        # copy over all stuff and run 
		f1.write("cd - \n");
		if options.doTraining: f1.write("mkdir weights \n")
		if options.makeROCs: 
			f1.write("mkdir plots \n")
			f1.write("for file in /eos/uscms/%s/o_*%s*.tar.gz; \n" % (eosweightdir,tag));
			f1.write("do \n");
			f1.write("	filebase=${file##*/} \n");
			f1.write("  echo $filebase \n");
			f1.write("	xrdcp root://cmseos.fnal.gov/%s/$filebase $filebase \n" % (eosweightdir) );
			f1.write("	tar -xvzf $filebase \n");
			f1.write("done \n");
		f1.write("cp %s/*.py . \n" % (startdir));
		f1.write("cp %s/tdrstyle.C . \n" % (startdir));
		f1.write("ls \n");
		f1.write(command+" \n")
		if options.doTraining:
			f1.write("tar -cvzf %s_%s.tar.gz weights \n" % (prefix,tag))
			f1.write("tar -cvzf %s_%s.tar.gz *.root \n" % (prefixR,tag))
			f1.write("xrdcp -f %s_%s.tar.gz root://cmseos.fnal.gov//store/user/ntran/SUSY/theory_JPM/training/%s_%s.tar.gz \n" % (prefix,tag,prefix,tag));
			f1.write("xrdcp -f %s_%s.tar.gz root://cmseos.fnal.gov//store/user/ntran/SUSY/theory_JPM/training/%s_%s.tar.gz \n" % (prefixR,tag,prefixR,tag));
		if options.makeROCs: 
			f1.write("tar -cvzf %s_%s.tar.gz plots \n" % (prefix,tag))
			f1.write("xrdcp -f %s_%s.tar.gz root://cmseos.fnal.gov//store/user/ntran/SUSY/theory_JPM/training/%s_%s.tar.gz \n" % (prefix,tag,prefix,tag));
		f1.write("rm *.py *.pyc *.tar.gz *.C \n");
		f1.close()

		f2n = "tmp_%s.condor" % (tag);
		outtag = "out_%s_$(Cluster)" % (tag)
		f2=open(f2n, 'w')
		f2.write("universe = vanilla \n");
		f2.write("Executable = %s \n" % (f1n) );
		f2.write("Requirements = Memory >= 199 &&OpSys == \"LINUX\"&& (Arch != \"DUMMY\" )&& Disk > 1000000 \n");
		f2.write("Should_Transfer_Files = YES \n");
		f2.write("WhenToTransferOutput  = ON_EXIT_OR_EVICT \n");
		f2.write("Output = "+outtag+".stdout \n");
		f2.write("Error = "+outtag+".stderr \n");
		f2.write("Log = "+outtag+".log \n");
		f2.write("Notification    = Error \n");
		f2.write("x509userproxy = $ENV(X509_USER_PROXY) \n")

		f2.write("Queue 1 \n");
		f2.close();

		os.system("condor_submit %s" % (f2n));

		os.chdir("../.");

##################################################################################################
##################################################################################################
##################################################################################################

if __name__ == '__main__':

	signals = [];
	#masses = ['500','1000','1500','2000'];
	masses = ['500','1000','1500'];
	# masses = ['1000','1500'];
	for i in range(1,5): 
		tag1,tag2 = "G","G";
		for ai in range(1,i+1): tag1+="j";
		for ai in range(1,i+1): tag2+="j";
		for m in masses: 
			signals.append( tag1+"N1_"+tag2+"N1__"+m+"_" );
			if i < 4: signals.append( tag1+"N1_"+tag2+"jN1__"+m+"_" );

	# signals = ['GjjjjN1_GjjjjN1__500_'];
	# backgrounds = ['ttbar']
	# backgrounds = ['Wjets']
	backgrounds = ['Wjets','QCD','znunu'];

	observables = [];
	observables.append( "HT" );
	observables.append( "MHT" );
	observables.append( "mEff" );
	observables.append( "NJets" );
	observables.append( "mT2" );
	observables.append( "MHTOvHT" );
	observables.append( "sumJetMass" );
	observables.append( "HT,NJets" );
	observables.append( "mRazor,dRazor" );
	observables.append( "sumJetMass,mT2" );
	observables.append( "NJets,mT2" );
	observables.append( "sumJetMass,MHT" );
	observables.append( "HT,NJets,MHT" );
	observables.append( "sumJetMass,NJets,MHT" );

	###########
	## training
	jobctr = 0;
	if options.doTraining:
		for sig in signals:
			for bkg in backgrounds:
				for obs in observables:
					command = "python analysis.py -b ";
					command += " --sampleDir " + sampleDir;
					command += " --weightDir " + weightDir;
					command += " --plotDir "   + plotDir;
					command += " --sigTag "     + sig;
					command += " --bkgTag "     + bkg;
					command += " --inputs "     + '"'+obs+'"';
					command += " --doTraining";

					print command;
					label = sig + "_" + bkg + "_" + obs;
					#tag = label.translate(None, ';,');
					labelbase = sig + "_" + bkg;
					tag = label.replace(',','_');
					tagbase = labelbase.replace(',','_')

					filestring = "%s/weights_bdtg_%s/TMVAClassification_MVA_bdtg_%s_BDTG.weights.xml" % (weightDir,tagbase,tag);
					if options.interactive:
						print "doing, ", command
						os.system(command);
					else:
						if not os.path.isfile(filestring) and options.cleaning: 
							jobctr+=1;
							condorize(command,tag);
						if not options.cleaning: 
							jobctr+=1; 
							condorize(command,tag);
						time.sleep(0.1) # delays for 5 seconds					

	## make roc
	if options.makeROCs:
		for sig in signals:
			for bkg in backgrounds:
				obsList = '';
				for iObs in range(len(observables)):
					if iObs != len(observables)-1: obsList += observables[iObs] + ";";
					else: obsList += observables[iObs];

				command = "python analysis.py -b ";
				command += " --sampleDir " + sampleDir;
				command += " --weightDir " + weightDir;
				command += " --plotDir "   + plotDir;
				command += " --sigTag "     + sig;
				command += " --bkgTag "     + bkg;
				command += " --inputs "     + '"'+obsList+'"';
				command += " --makeROCs";

				print command;
				label = sig + "_" + bkg + "_ROCs";
				#tag = label.translate(None, ';,');
				labelbase = sig + "_" + bkg;
				tag = label.replace(',','_');
				tagbase = labelbase.replace(',','_')

				filestring = "%s/plots_bdtg_%s/RocSummary_%s.txt" % (plotDir,tagbase,tagbase);
				#print filestring
				# print tag;	
				# condorize(command,tag);
				if options.interactive:
					print "interactively: ", command, tagbase
					os.system(command);
				else:
					if not os.path.isfile(filestring) and options.cleaning: 
						jobctr+=1;
						condorize(command,tagbase);
					if not options.cleaning: 
						jobctr+=1; 
						condorize(command,tagbase);
					time.sleep(0.1) # delays for 5 seconds					

	print "total jobs = ", jobctr;
