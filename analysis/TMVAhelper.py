#! /usr/bin/env python
import os
import glob
import math
from array import array
import sys
import time

import ROOT

from ROOT import *
from array import array

class TMVAhelper:
	
	# -------------------------------------
	def __init__(self,named,inputVars,trees,spectators,weightloc='weights'):

		self._named = named;
		self._inputVars = inputVars;
		self._trees = trees;
		self._nInputVars = len(self._inputVars);
		self._spectators = spectators

		## classifier
		## inputs, list of variables, list of ntuples
		fout = ROOT.TFile(self._named+".root","RECREATE")        
		self._factory = ROOT.TMVA.Factory("TMVAClassification_"+self._named, fout,
									":".join(["!V",
											  "!Silent",
											  "Color",
											  "DrawProgressBar",
											  "Transformations=I",
											  "AnalysisType=Classification"]
											 ));      

		self._weightloc = weightloc;
		ROOT.TMVA.gConfig().GetIONames().fWeightFileDir = self._weightloc;
		
		self._reader = ROOT.TMVA.Reader()
		self._varRefs = [];
		self._specRefs = [];

		print "self._weightloc = ",self._weightloc

	# -------------------------------------    
	def train(self,cutstring):
		
		print "training..."
		
		# define inputs
		for i in range(self._nInputVars):
			self._factory.AddVariable(self._inputVars[i],"F");
		for variables in self._spectators: 
			self._factory.AddSpectator(variables,"F");


		self._factory.AddSignalTree( self._trees[0] );
		for i in range(1,len(self._trees)): self._factory.AddBackgroundTree( self._trees[i] );

		#cutstring = "(jpt[0] > "+str(ptlo)+") && (jpt[0] < "+str(pthi)+")";
		cuts = ROOT.TCut(cutstring);
		self._factory.SetSignalWeightExpression( "lheWeight" )
		self._factory.SetBackgroundWeightExpression( "lheWeight" )

		self._factory.PrepareTrainingAndTestTree(cuts,   # signal events
										   ":".join([
													 "nTrain_Signal=0",
													 "nTrain_Background=0",
													 "SplitMode=Random",
													 "NormMode=NumEvents",
													 "!V"
													 ]));

		###method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=500:BoostType=Grad:Shrinkage=0.10:UseBaggedGrad=F:nCuts=25000:MaxDepth=3:SeparationType=GiniIndex");
		###if self._inputVars <= 2: method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=500:BoostType=Grad:Shrinkage=0.10:UseBaggedGrad=F:nCuts=25000:MaxDepth=3:SeparationType=GiniIndex");
		###else:                    method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=1000:BoostType=Grad:Shrinkage=0.10:UseBaggedGrad=F:nCuts=25000:MaxDepth=5:SeparationType=GiniIndex");
		###method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=400:BoostType=Grad:Shrinkage=0.1:UseBaggedGrad=F:nCuts=2000:NNodesMax=10000:MaxDepth=5:UseYesNoLeaf=F:nEventsMin=200");
		method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=400:BoostType=Grad:Shrinkage=0.1:UseBaggedGrad=F:nCuts=1000:MaxDepth=3:UseYesNoLeaf=F:nEventsMin=200")
		
		#### method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=200:BoostType=Grad:Shrinkage=0.10:UseBaggedGrad=F:nCuts=200:MaxDepth=5:SeparationType=GiniIndex");
		#method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=100:MinNodeSize=0.025:BoostType=Grad:Shrinkage=0.10:UseBaggedBoost:BaggedSampleFraction=0.5:nCuts=20:MaxDepth=4");
		
		#from cv
		# method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"BDTG","!H:!V:NTrees=300:BoostType=Grad:Shrinkage=0.10:UseBaggedGrad=F:nCuts=30:MaxDepth=3:SeparationType=GiniIndex");


		##method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"Cuts","!H:!V:FitMethod=MC:EffSel:SampleSize=200000:VarProp=FSmart");
		#method = self._factory.BookMethod(ROOT.TMVA.Types.kBDT,"Cuts","!H:!V");#:EffSel:SampleSize=200000:VarProp=FSmart");

		self._factory.TrainAllMethods()
		self._factory.TestAllMethods()
		self._factory.EvaluateAllMethods()
		
		
	# -------------------------------------    
	def read(self,method="BDT"):
	
		for i in range(self._nInputVars): self._varRefs.append( array('f',[0]) );
		for i in range(len(self._spectators)): self._specRefs.append( array('f',[0]) );
		
		for i in range(self._nInputVars):
			self._reader.AddVariable(self._inputVars[i],self._varRefs[i]);     
		for i in range(len(self._spectators)):
			self._reader.AddSpectator(self._spectators[i],self._specRefs[i]); 

		weightFile = self._weightloc+"/TMVAClassification_"+self._named+"_"+method+".weights.xml";
		# weightFile = "TMVAClassification_"+self._named+"_"+method+".weights.xml";
		print "weightFile = ", weightFile
		self._reader.BookMVA(method,weightFile)        
		# self._reader.BookMVA(method,"TMVAClassification_"+self._named+"_"+method+".weights.xml")        
		#self._reader.BookMVA("BDT","weights/TMVAClassification_BDT.weights.xml")        
		
	# -------------------------------------            
	def evaluate(self,val,method="BDT"):
			
		for i in range(self._nInputVars):
			self._varRefs[i][0] = val[i];  
		
		bdtOutput = self._reader.EvaluateMVA(method)
		return bdtOutput;      
		