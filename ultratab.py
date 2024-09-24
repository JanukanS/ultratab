from dataclasses import dataclass
from functools import cached_property, partialmethod
import ipywidgets as widgets
from inspect import signature
from itertools import product

@dataclass
class TabView:
    tabDict: dict

    @cached_property
    def TabChildren(self):
        outList = []
        for _, tbFunc in self.tabDict.items():
            outList.append(widgets.Output())
            with outList[-1]:
                if type(tbFunc) == dict:
                    display(TabView(tbFunc).Tab)
                else:
                    tbFunc()
        return outList

    @cached_property
    def Tab(self):
        tb = widgets.Tab()
        tb.children = self.TabChildren
        tab_titles = list(self.tabDict.keys())
        for ind, tt in enumerate(tab_titles):
            tb.set_title(ind, tt)
        return tb

class InteractivePlotGen:

    @classmethod
    def extractSliders(cls, genObj, genPlotFunc):
        """get the sliders required for the interactive widget"""
        argCont = genPlotFunc.__code__.co_argcount
        argList = genPlotFunc.__code__.co_varnames[1:argCont]
        return {argName: getattr(genObj, argName) for argName in argList}


    @classmethod
    def plotMethod(cls, genObj, genPlotFunc):
        """Create and display an interactive widget based on an object method"""
        sliders = cls.extractSliders(genObj, genPlotFunc)
        opw = widgets.Output()
        def plotFunc(**kwargs):
            opw.clear_output()
            with opw:
                genPlotFunc(**kwargs)

        intWidget = widgets.interactive(plotFunc, {"manual": True},**sliders)
        combWidgets = widgets.VBox([intWidget, opw])
        display(combWidgets)

class TabGen:
    @staticmethod
    def MethodLocatorGenerator(methodClass):
        return lambda methodName: getattr(methodClass, methodName).__code__.co_firstlineno

    @classmethod
    def extractPlotMethods(cls, obj):
        plotParse = lambda val: "plot" in val and val[:4] == "plot"
        plotAttrs = [val for val in dir(obj) if plotParse(val)]
        methodLocFunc = cls.MethodLocatorGenerator(type(obj))
        plotAttrs.sort(key=methodLocFunc)
        plotNames = [val[4:] for val in plotAttrs]
        plotPair = {nameVal: getattr(obj, attrVal) for nameVal, attrVal in zip(plotNames, plotAttrs)}
        return plotPair

    @classmethod
    def extractGenPlotMethods(cls, obj):
        genPlotParse = lambda val: "genPlot" in val and val[:7] == "genPlot"
        genPlotAttrs = [val for val in dir(obj) if genPlotParse(val)]
        methodLocFunc = cls.MethodLocatorGenerator(type(obj))
        genPlotAttrs.sort(key=methodLocFunc)
        genPlotNames = [val[7:] for val in genPlotAttrs]
        funcGen = lambda obj, attrName: lambda: InteractivePlotGen.plotMethod(obj, getattr(obj, attrName))
        genPlotPair = {nameVal: funcGen(obj, attrVal) for nameVal, attrVal in zip(genPlotNames, genPlotAttrs)}
        return genPlotPair

    @classmethod
    def extractDict(cls, obj):
        plotPair = cls.extractPlotMethods(obj)
        plotPair.update(cls.extractGenPlotMethods(obj))
        return plotPair

    @classmethod
    def generate(cls, objDict: dict):
        tabDict = {}
        for key, val in objDict.items():
            tabDict[key] = cls.extractDict(val)
        return TabView(tabDict)

    @classmethod
    def plot(cls, objDict: dict):
        TabObj = cls.generate(objDict)
        display(TabObj.Tab)
