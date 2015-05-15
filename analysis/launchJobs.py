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
parser.add_option('--makeROCs', action='store_true', dest='makeROCs', default=False, help='training or not')

(options, args) = parser.parse_args()


def condorize(command,tag):

		print "--------------------"
		print "Processing sample..."

		#change to a tmp dir
		if not os.path.exists('tmp'): os.makedirs('tmp');
		os.chdir("tmp");
		curdir = os.getcwd();

		f1n = "tmp_%s.sh" %(tag);
		f1=open(f1n, 'w')
		f1.write("#!/bin/sh \n");
		f1.write("source /cvmfs/cms.cern.ch/cmsset_default.csh \n");
		f1.write("set SCRAM_ARCH=slc6_amd64_gcc481\n")
		f1.write("cd /uscms_data/d2/ntran/physics/SUSY/Run2/combination/CMSSW_7_2_0/src/ \n")
		f1.write("eval `scramv1 runtime -sh`\n")
		f1.write("cd %s \n" % (curdir))
		f1.write("cd .. \n")                
		f1.write(command)
		#f.write("cd Sens3/ \n")
		#f1.write("cd %s \n" % (workDir))
		#f1.write("%s %s %s -s %d -n %sSig%dCombine%d  \n" %(basecommand, datacard, options, r,testname,j,i))
		f1.close()

		f2n = "tmp_%s.condor" %(tag);
		f2=open(f2n, 'w')
		f2.write("universe = vanilla \n");
		f2.write("Executable = %s \n" % (f1n) );
		f2.write("Requirements = Memory >= 199 &&OpSys == \"LINUX\"&& (Arch != \"DUMMY\" )&& Disk > 1000000 \n");
		f2.write("Should_Transfer_Files = YES \n");
		f2.write("WhenToTransferOutput  = ON_EXIT_OR_EVICT \n");
		f2.write("Output = out_$(Cluster).stdout \n");
		f2.write("Error = out_$(Cluster).stderr \n");
		f2.write("Log = out_$(Cluster).log \n");
		f2.write("Notification    = Error \n");
		f2.write("Queue 1 \n");
		f2.close();

		os.system("condor_submit %s" % (f2n));

		os.chdir("../.");

if __name__ == '__main__':

	sampleDir = '/uscms_data/d2/ntran/physics/SUSY/theory/JPM/processFiles/samples/';
	weightDir = '/eos/uscms/store/user/ntran/SUSY/theory_JPM/training/weights';
	plotDir   = '/eos/uscms/store/user/ntran/SUSY/theory_JPM/training/plots';

	signals = [];
	masses = ['500','1000','1500','2000'];
	for i in range(1,5): 
		tag1,tag2 = "G","G";
		for ai in range(1,i+1): tag1+="j";
		for ai in range(1,i+1): tag2+="j";
		for m in masses: 
			signals.append( tag1+"N1_"+tag2+"N1__"+m+"_" );
			if i < 4: signals.append( tag1+"N1_"+tag2+"jN1__"+m+"_" );
		
	backgrounds = ['ttbar','Wjets','QCD'];

	# signals = ['GjjjjN1_GjjjjN1__1000_'];
	# backgrounds = ['Wjets']

	observables = [];
	observables.append( "HT" );
	observables.append( "MHT" );
	observables.append( "NJets" );
	observables.append( "HT,MHT" );
	observables.append( "NJets,MHT" );
	observables.append( "HT,NJets" );
	observables.append( "HT,NJets,MHT" );

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

					# print command;
					label = sig + "_" + bkg + "_" + obs;
					tag = label.translate(None, ';,');
					# print tag;	
					condorize(command,tag);
					jobctr+=1;
	print "total jobs = ", jobctr;

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

				# print command;
				label = sig + "_" + bkg + "_ROCs";
				tag = label.translate(None, ';,');
				# print tag;	
				condorize(command,tag);

