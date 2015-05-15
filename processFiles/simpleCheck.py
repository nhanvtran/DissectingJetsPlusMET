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

	f = ROOT.TFile("tmp/ProcJPM_QCD.root");
	t = f.Get("otree");

	h_HT = ROOT.TH1F("h_HT",";HT (GeV);Events",100,0,10000);
	h_MHT = ROOT.TH1F("h_MHT",";MHT (GeV);Events",100,0,1000);

	nent = t.GetEntriesFast();
	for i in range(t.GetEntriesFast()):
		if(i % (1 * nent/100) == 0):
			sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done");
			sys.stdout.flush();

		t.GetEntry(i);
		h_HT.Fill(t.HT,t.lheWeight);
		h_MHT.Fill(t.MHT,t.lheWeight);
	print '\n'

	c_HT = ROOT.TCanvas("c_HT","c_HT",1000,800);
	h_HT.Draw();
	ROOT.gPad.SetLogy();
	c_HT.SaveAs("plots/HT.pdf");

	c_MHT = ROOT.TCanvas("c_MHT","c_MHT",1000,800);
	h_MHT.Draw();
	ROOT.gPad.SetLogy();
	c_MHT.SaveAs("plots/MHT.pdf");
