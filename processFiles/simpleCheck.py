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

if __name__ == '__main__':

	# f = ROOT.TFile("tmp/ProcJPM_QCD-test.root");
	#f = ROOT.TFile("../localData/Backgrounds/Backgrounds_13TEV/Znunu/slim_znunu_0_400_18385.root");
	f = ROOT.TFile("samples-raw/ProcJPM_znunu.root")
	t = f.Get("otree");

	h_HT = ROOT.TH1F("h_HT",";HT (GeV);Events",100,0,10000);
	h_MHT = ROOT.TH1F("h_MHT",";MHT (GeV);Events",100,0,1000);
	h_sumJetMass = ROOT.TH1F("h_sumJetMass",";sumJetMass (GeV);Events",100,0,3000);
	h_MT2 = ROOT.TH1F("h_MT2",";MT2 (GeV);Events",100,0,5000);

	nent = t.GetEntriesFast();
	for i in range(t.GetEntriesFast()):

		# if(i % (1 * nent/100) == 0):
		# 	sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done");
		# 	sys.stdout.flush();

		t.GetEntry(i);
		h_HT.Fill(t.HT,t.lheWeight);
		h_MHT.Fill(t.MHT,t.lheWeight);
		h_sumJetMass.Fill(t.sumJetMass,t.lheWeight);
		h_MT2.Fill(t.mT2,t.lheWeight);
		print t.mT2, t.alphaT, t.dRazor, t.mRazor, t.sumJetMass

	print '\n'

	c_HT = ROOT.TCanvas("c_HT","c_HT",1000,800);
	h_HT.Draw();
	ROOT.gPad.SetLogy();
	c_HT.SaveAs("plots/HT.pdf");

	c_MHT = ROOT.TCanvas("c_MHT","c_MHT",1000,800);
	h_MHT.Draw();
	ROOT.gPad.SetLogy();
	c_MHT.SaveAs("plots/MHT.pdf");

	c_sumJetMass = ROOT.TCanvas("c_sumJetMass","c_sumJetMass",1000,800);
	h_sumJetMass.Draw();
	ROOT.gPad.SetLogy();
	c_sumJetMass.SaveAs("plots/sumJetMass.pdf");

	c_MT2 = ROOT.TCanvas("c_MT2","c_MT2",1000,800);
	h_MT2.Draw();
	ROOT.gPad.SetLogy();
	c_MT2.SaveAs("plots/MT2.pdf");

