#! /usr/bin/env python
import os
import glob
import math
from array import array
import sys
import time

import ROOT

from observableContainer import *
from TMVAhelper import *
from utilities import *

ROOT.gROOT.ProcessLine(".L tdrstyle.C");
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

parser.add_option('--doTraining', action='store_true', dest='doTraining', default=False, help='training or not')
parser.add_option('--makeROCs', action='store_true', dest='makeROCs', default=False, help='training or not')

parser.add_option('--inputs',action="store",type="string",dest="inputs",default="HT")
parser.add_option('--sampleDir',action="store",type="string",dest="sampleDir",default="/uscms_data/d2/ntran/physics/SUSY/theory/JPM/processFiles/samples-v1/")
parser.add_option('--sigTag',action="store",type="string",dest="sigTag",default="GjN1_GjN1__2000_")
parser.add_option('--bkgTag',action="store",type="string",dest="bkgTag",default="ttbar")
parser.add_option('--weightDir',action="store",type="string",dest="weightDir",default="/eos/uscms/store/user/ntran/SUSY/theory_JPM/training/weights")
parser.add_option('--plotDir',action="store",type="string",dest="plotDir",default="/eos/uscms/store/user/ntran/SUSY/theory_JPM/training/plots")

(options, args) = parser.parse_args()

############################################################

# observableTraining takes in 2 root files, list of observables, spectator observables ... launches a CONDOR job
# TMVAhelper.py is used by observableTraining
# analysis.py defines the list of trainings, the signal and background process

########################################################################################################################
########################################################################################################################

if __name__ == '__main__':

	weightloc = options.weightDir;
	odir = options.plotDir;

	sampleDir = options.sampleDir;
	sigName = options.sigTag;
	bkgName = options.bkgTag;
	sigFN = sampleDir+"/"+"ProcJPM_"+sigName+".root"
	bkgFN = sampleDir+"/"+"ProcJPM_"+bkgName+".root"

	variables = [];
	for ivars in options.inputs.split(';'): 
		variables.append( ivars.split(',') );
	print variables
	
	f_sig = ROOT.TFile(sigFN);
	f_bkg = ROOT.TFile(bkgFN);    
	t_sig = f_sig.Get("otree");
	t_bkg = f_bkg.Get("otree");

	cuts = [];
	cuts.append( ["HT",500,99999] );
	cuts.append( ["MHT",200,99999] );
	cuts.append( ["NJets",2,99] );

	allVariables = ["HT","NJets","MHT"];
	varlo        = [   0,      0,    0];
	varhi        = [6000,     20, 1000];
	h_variables = [];
	for i in range(len(allVariables)): 
		h_variables.append( [ROOT.TH1F("hs_"+allVariables[i],"au; "+allVariables[i]+";",20,varlo[i],varhi[i]), ROOT.TH1F("hb_"+allVariables[i],"au; "+allVariables[i]+";",20,varlo[i],varhi[i]) ] );

	# variables = [];
	# variables.append( ["HT"] );
	# # variables.append( ["NJets"] );
	# # variables.append( ["MHT"] );
	# # variables.append( ["HT","MHT"] );
	# # variables.append( ["HT","NJets"] );
	# # variables.append( ["NJets","MHT"] );
	# # variables.append( ["HT","NJets","MHT"] );
	# spectators = [];

	observableSets = [];
	h_bdts = [];
	labelbase = "bdtg_%s_%s" % (sigName,bkgName);
	curodir = odir + "/" + "plots_" + labelbase;
	if options.makeROCs: 
		if not os.path.exists(curodir): os.makedirs(curodir);
	
	for i in range(len(variables)):
		label = labelbase;
		for vnames in variables[i]: label += "_" + vnames;

		curweightloc = weightloc+"/" + "weights_" + labelbase;
		if options.doTraining: 
			if not os.path.exists(curweightloc): os.makedirs(curweightloc);

		observableSets.append( observableContainer(sigFN,bkgFN,variables[i],cuts,label,curweightloc) );
		if options.doTraining: observableSets[i].doTraining();
		observableSets[i].readMVA("BDTG");
		h_bdts.append( [ROOT.TH1F("hsbdt_"+label,"au; "+label+";",1000,-1,1), ROOT.TH1F("hbbdt_"+label,"au; "+label+";",1000,-1,1) ] );

	##### ##### ##### ##### ##### 
	# FILL TREES
	if options.makeROCs:

		trees = [t_sig,t_bkg];
		names = [sigName,bkgName];
		for it in range(len(trees)):
			nent = trees[it].GetEntriesFast()
			for i in range(nent):
				
				# if i > 100000: break;

				if(i % (1 * nent/100) == 0):
					sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done");
					sys.stdout.flush();


				trees[it].GetEntry(i);

				# print "lheWeight = ", trees[it].lheWeight

				passesCuts = True;
				for cut in cuts:
					if getattr(trees[it],cut[0]) < cut[1] or getattr(trees[it],cut[0]) > cut[2]: passesCuts = False;
				if passesCuts == False: continue; 

				# fill the variable histograms
				for ivar in range(len(allVariables)): 
					# print getattr(trees[it],allVariables[ivar]), getattr(trees[it],"lheWeight") ;
					h_variables[ivar][it].Fill( getattr(trees[it],allVariables[ivar]), getattr(trees[it],"lheWeight") );
				# fill the bdt histograms
				for ibdt in range(len(variables)): 
					tmplist = [];
					for var in variables[ibdt]: tmplist.append( getattr(trees[it],var) );
					h_bdts[ibdt][it].Fill( observableSets[ibdt].evaluateMVA(tmplist,"BDTG"), getattr(trees[it],"lheWeight") );

			print "\n";

	##### ##### ##### ##### ##### 
	# PLOT

		for ivar in range(len(allVariables)): makeCanvas(h_variables[ivar],names,allVariables[ivar],curodir,True);
		for ibdt in range(len(variables)): 
			label = "bdt_";
			for vnames in variables[ibdt]: label += vnames + "_";
			makeCanvas(h_bdts[ibdt],names,label,curodir,True);

	##### ##### ##### ##### ##### 
	# make ROCs		
		rocs = [];
		leg = ROOT.TLegend( 0.2, 0.6, 0.5, 0.9 );
		leg.SetBorderSize( 0 );
		leg.SetFillStyle( 0 );
		leg.SetTextSize( 0.03 );        
		for ibdt in range(len(variables)):
			rocs.append( makeROCFromHisto(h_bdts[ibdt]) );
			rocs[ibdt].SetLineColor(ibdt+1);
			rocs[ibdt].SetLineWidth(2)
			label = "";
			for ivar in range(len(variables[ibdt])): 
				label += str(variables[ibdt][ivar]);
				if ivar < len(variables[ibdt])-1: label += "+";

			leg.AddEntry( rocs[ibdt], label, "l" );

		canroc = ROOT.TCanvas("canroc","canroc",1200,1000);
		hrl1 = canroc.DrawFrame(1e-1,1e-4,1.0,1.0);
		# hrl1.GetXaxis().SetTitle("#varepsilon_{sig} ("+signame+")");
		# hrl1.GetYaxis().SetTitle("#varepsilon_{bkg} ("+bkgname+")");
		hrl1.GetXaxis().SetTitle("signal efficiency");
		hrl1.GetYaxis().SetTitle("background efficiency");
		for i in range(len(rocs)): rocs[i].Draw("l");

		leg.Draw();
		canroc.SaveAs(curodir+"/Rocs.root");
		canroc.SaveAs(curodir+"/Rocs.eps");
		canroc.SaveAs(curodir+"/Rocs.png");
		ROOT.gPad.SetLogy();
		ROOT.gPad.SetLogx();
		canroc.SaveAs(curodir+"/Rocs_log.root");
		canroc.SaveAs(curodir+"/Rocs_log.eps");
		canroc.SaveAs(curodir+"/Rocs_log.png");








