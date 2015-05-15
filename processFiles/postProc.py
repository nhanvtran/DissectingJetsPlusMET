#! /usr/bin/env python
import os
import glob
import math
from array import array
import sys
import time

import ROOT

ROOT.gROOT.ProcessLine(".L ~/tdrstyle.C");
ROOT.setTDRStyle();
ROOT.gStyle.SetPadTopMargin(0.06);
ROOT.gStyle.SetPadLeftMargin(0.16);
ROOT.gStyle.SetPadRightMargin(0.10);
ROOT.gStyle.SetPalette(1);
ROOT.gStyle.SetPaintTextFormat("1.1f");

############################################
#            Job steering                  #
############################################
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-b', action='store_true', dest='noX', default=False, help='no X11 windows')

parser.add_option('--sigFN',action="store",type="float",dest="mhtHi",default=9999)
parser.add_option('--bigFN',action="store",type="float",dest="njLo",default=3)
parser.add_option('--njHi',action="store",type="float",dest="njHi",default=99)

parser.add_option('--signame',action="store",type="string",dest="signame",default="T1tttt1500-100")
parser.add_option('--bkgname',action="store",type="string",dest="bkgname",default="QCD")

(options, args) = parser.parse_args()

############################################################

# observableTraining takes in 2 root files, list of observables, spectator observables ... launches a CONDOR job
# TMVAhelper.py is used by observableTraining
# analysis.py defines the list of trainings, the signal and background process

########################################################################################################################
########################################################################################################################

def getSampleXS(name):

	xs = -999;
	if 'ttbar' in name and '0_600' in name: xs = 447.49;
	elif 'ttbar' in name and '600_1200' in name: xs = 31.10;
	elif 'ttbar' in name and '1200_1900' in name: xs = 1.97;
	elif 'ttbar' in name and '1900_2700' in name: xs = 0.16;
	elif 'ttbar' in name and '2700_3600' in name: xs = 0.015;
	elif 'ttbar' in name and '3600_4600' in name: xs = 0.0015;
	elif 'ttbar' in name and '4600_100000' in name: xs = 1.37e-4;

	elif 'Wjets' in name and '0_600' in name: xs = 1846.16;
	elif 'Wjets' in name and '600_1200' in name: xs = 94.80;
	elif 'Wjets' in name and '1200_2000' in name: xs = 6.03;
	elif 'Wjets' in name and '2000_3000' in name: xs = 0.46;
	elif 'Wjets' in name and '3000_4100' in name: xs = 0.036;
	elif 'Wjets' in name and '4100_5200' in name: xs = 0.0030;
	elif 'Wjets' in name and '5200_100000' in name: xs = 3.01e-4;

	elif 'QCD' in name and '0_400' in name: xs = 1.18e6;
	elif 'QCD' in name and '400_800' in name: xs = 6.09e4;
	elif 'QCD' in name and '800_1300' in name: xs = 2550.0;
	elif 'QCD' in name and '1300_2000' in name: xs = 196.0;
	elif 'QCD' in name and '2000_2900' in name: xs = 14.7;
	elif 'QCD' in name and '2900_3900' in name: xs = 1.06;
	elif 'QCD' in name and '3900_4900' in name: xs = 8.71e-2;
	elif 'QCD' in name and '4900_5900' in name: xs = 8.51e-3;
	elif 'QCD' in name and '5900_6900' in name: xs = 8.47e-4;
	elif 'QCD' in name and '6900_100000' in name: xs = 8.46e-5;

	elif 'Gj' in name: xs = -999;

	else: 
		raise NameError("too many keys!")
		return;		

	return xs;

def getLHEWeight(files):
	
	print "processing: ",files[0]
	theXS = getSampleXS(files[0])
	totalEvents = 0;

	for f in files:
		f1 = ROOT.TFile(f,'read');
		thekey = None;
		if len(ROOT.gDirectory.GetListOfKeys()) > 1: 
			raise NameError("too many keys!")
			return;
		for key in ROOT.gDirectory.GetListOfKeys(): thekey = key;
		tree = thekey.ReadObj();
		totalEvents += tree.GetEntriesFast();

	print totalEvents, theXS;
	if theXS == -999: return 1;
	else: return (theXS/totalEvents)

def slimSkimAdd(fn,odir,weight):

	basename = os.path.basename( fn );

	f1 = ROOT.TFile(fn,'read');
	thekey = None;

	if len(ROOT.gDirectory.GetListOfKeys()) > 1: 
		raise NameError("too many keys!")
		return;

	for key in ROOT.gDirectory.GetListOfKeys(): thekey = key;
	tree = thekey.ReadObj();

	ofile = ROOT.TFile(odir+'/'+basename,'RECREATE');
	ofile.cd();
	otree = tree.CloneTree(0);
	otree.SetName("otree");

	lheWeight = array( 'f', [ 0. ] );  
	b_lheWeight = otree.Branch("lheWeight",lheWeight,"lheWeight/F"); #xs*lumi/nev, take lumi as 1fb-1

	nent = tree.GetEntriesFast();
	for i in range(nent):

		# if(i % (1 * nent/100) == 0):
		# 	sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done");
		# 	sys.stdout.flush();

		tree.GetEntry(i);
		lheWeight[0] = float(weight);

		#if tree.HT > 500 and tree.NJets > 2 and tree.MHT > 0:
		otree.Fill();   

	#print "\n"
	#otree.Print();
	otree.AutoSave();
	ofile.cd();
	otree.Write();
	ofile.Close();

def getFilesRecursively(dir,searchstring,additionalstring = None):
	
	cfiles = [];
	for root, dirs, files in os.walk(DataDir):
		for file in files:	
			if searchstring in file:
				if additionalstring == None or additionalstring in file:
					cfiles.append(os.path.join(root, file))
	return cfiles;

if __name__ == '__main__':

	DataDir = "/uscms_data/d2/ntran/physics/SUSY/theory/JPM/Data";
	OutDir = 'tmp';

	tags = [];
	tags.append( ['ttbar','0_600'] );
	tags.append( ['ttbar','600_1200'] );
	tags.append( ['ttbar','1200_1900'] );
	tags.append( ['ttbar','1900_2700'] );
	tags.append( ['ttbar','2700_3600'] );
	tags.append( ['ttbar','3600_4600'] );
	tags.append( ['ttbar','4600_100000'] );
	tags.append( ['Wjets','0_600'] );
	tags.append( ['Wjets','600_1200'] );
	tags.append( ['Wjets','1200_2000'] );
	tags.append( ['Wjets','2000_3000'] );
	tags.append( ['Wjets','3000_4100'] );
	tags.append( ['Wjets','4100_5200'] );
	tags.append( ['Wjets','5200_100000'] );
	tags.append( ['QCD','0_400'] );
	tags.append( ['QCD','400_800'] );
	tags.append( ['QCD','800_1300'] );
	tags.append( ['QCD','1300_2000'] );
	tags.append( ['QCD','2000_2900'] );
	tags.append( ['QCD','2900_3900'] );
	tags.append( ['QCD','3900_4900'] );
	tags.append( ['QCD','4900_5900'] );
	tags.append( ['QCD','5900_6900'] );
	tags.append( ['QCD','6900_100000'] );

	tags.append( ['GjN1_GjN1',       '_500_'] );
	tags.append( ['GjN1_GjjN1',      '_500_'] );
	tags.append( ['GjjN1_GjjN1',     '_500_'] );
	tags.append( ['GjjN1_GjjjN1',    '_500_'] );
	tags.append( ['GjjjN1_GjjjN1',   '_500_'] );
	tags.append( ['GjjjN1_GjjjjN1',  '_500_'] );
	tags.append( ['GjjjjN1_GjjjjN1', '_500_'] );
	tags.append( ['GjN1_GjN1',      '_1000_'] );
	tags.append( ['GjN1_GjjN1',     '_1000_'] );
	tags.append( ['GjjN1_GjjN1',    '_1000_'] );
	tags.append( ['GjjN1_GjjjN1',   '_1000_'] );
	tags.append( ['GjjjN1_GjjjN1',  '_1000_'] );
	tags.append( ['GjjjN1_GjjjjN1', '_1000_'] );
	tags.append( ['GjjjjN1_GjjjjN1','_1000_'] );
	tags.append( ['GjN1_GjN1',      '_1500_'] );
	tags.append( ['GjN1_GjjN1',     '_1500_'] );
	tags.append( ['GjjN1_GjjN1',    '_1500_'] );
	tags.append( ['GjjN1_GjjjN1',   '_1500_'] );
	tags.append( ['GjjjN1_GjjjN1',  '_1500_'] );
	tags.append( ['GjjjN1_GjjjjN1', '_1500_'] );
	tags.append( ['GjjjjN1_GjjjjN1','_1500_'] );
	tags.append( ['GjN1_GjN1',      '_2000_'] );
	tags.append( ['GjN1_GjjN1',     '_2000_'] );
	tags.append( ['GjjN1_GjjN1',    '_2000_'] );
	tags.append( ['GjjN1_GjjjN1',   '_2000_'] );
	tags.append( ['GjjjN1_GjjjN1',  '_2000_'] );
	tags.append( ['GjjjN1_GjjjjN1', '_2000_'] );
	tags.append( ['GjjjjN1_GjjjjN1','_2000_'] );


	# make a tmp dir
	#####

	for i in range(len(tags)):
		
		filesToConvert = getFilesRecursively(DataDir,tags[i][0],tags[i][1]);
		#print filesToConvert
		curweight = getLHEWeight( filesToConvert );
		for f in filesToConvert:
			slimSkimAdd(f,OutDir,curweight);
		## hadd stuff
		oname = OutDir + '/ProcJPM_'+tags[i][0]+"_"+tags[i][1]+".root";
		haddCmmd = 'hadd -f '+oname+" ";
		for f in filesToConvert:
			ofile = OutDir + "/" + os.path.basename( f );
			haddCmmd += ofile + " ";
		print haddCmmd;
		os.system(haddCmmd);

	for files in os.listdir(OutDir):
		if 'slim' in files: os.system('rm '+OutDir+'/'+files)

	cmmd = 'hadd -f %s/ProcJPM_ttbar.root %s/*ttbar*.root' % (OutDir,OutDir)
	os.system(cmmd)
	cmmd = 'hadd -f %s/ProcJPM_Wjets.root %s/*Wjets*.root' % (OutDir,OutDir)
	os.system(cmmd)
	cmmd = 'hadd -f %s/ProcJPM_QCD.root %s/*QCD*.root' % (OutDir,OutDir)
	os.system(cmmd)






